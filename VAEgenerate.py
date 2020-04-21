import ctypes.util
import fluidsynth
import magenta
import magenta.music as mm
import numpy as np
import os
import tempfile
import tensorflow as tf
import warnings

from magenta.models.music_vae import configs
from magenta.models.music_vae.trained_model import TrainedModel

# https://github.com/tensorflow/magenta/tree/master/magenta/models/music_vae


def proxy_find_library(lib):
    if lib == 'fluidsynth':
        return 'libfluidsynth.so.1'
    else:
        return orig_ctypes_util_find_library(lib)

# # Necessary until pyfluidsynth is updated (>1.2.5).
# warnings.filterwarnings("ignore", category=DeprecationWarning)
# orig_ctypes_util_find_library = ctypes.util.find_library
# ctypes.util.find_library = proxy_find_library


def play(note_sequence):
    mm.play_sequence(note_sequence, synth=mm.fluidsynth)


def interpolate(model, start_seq, end_seq, num_steps, max_length=32,
                assert_same_length=True, temperature=0.5,
                individual_duration=4.0):
    """Interpolates between a start and end sequence."""
    note_sequences = model.interpolate(
        start_seq, end_seq,num_steps=num_steps, length=max_length,
        temperature=temperature,
        assert_same_length=assert_same_length)
    interp_seq = mm.sequences_lib.concatenate_sequences(
        note_sequences, [individual_duration] * len(note_sequences))

    return interp_seq if num_steps > 3 else note_sequences[num_steps // 2]


def note_sequence_to_midi_file(sequence, output_file,
                               drop_events_n_seconds_after_last_note=None):
    """
    Convert NoteSequence to a MIDI file on disk.
    Time is stored in the NoteSequence in absolute values (seconds) as opposed to
    relative values (MIDI ticks). When the NoteSequence is translated back to
    MIDI the absolute time is retained. The tempo map is also recreated.
    Args:
    sequence: A NoteSequence.
    output_file: String path to MIDI file that will be written.
    drop_events_n_seconds_after_last_note: Events (e.g., time signature changes)
        that occur this many seconds after the last note will be dropped. If
        None, then no events will be dropped.
    """
    pretty_midi_object = mm.midi_io.note_sequence_to_pretty_midi(sequence, drop_events_n_seconds_after_last_note)
    
    with tempfile.NamedTemporaryFile() as temp_file:
        pretty_midi_object.write(temp_file)
        # Before copying the file, flush any contents
        temp_file.flush()
        # And back the file position to top (not need for Copy but for certainty)
        temp_file.seek(0)
        tf.gfile.Copy(temp_file.name, output_file, overwrite=True)


def set_config(alg):
    """
    alg is a string
    can be either of alg listed here:
    https://github.com/tensorflow/magenta/tree/master/magenta/models/music_vae
    now we have
    hierdec_trio_16bar, aseline_flat_trio_16bar, cat-drums_2bar_small
    """
    trio_models = {}
    if alg == 'hierdec-trio_16bar':
        hierdec_trio_16bar_config = configs.CONFIG_MAP['hierdec-trio_16bar']
        config = hierdec_trio_16bar_config
        trio_models['hierdec_trio_16bar'] = TrainedModel(config, 
            batch_size=4, checkpoint_dir_or_path='./VAE/checkpoints/trio_16bar_hierdec.ckpt')

        #@title Option 1: Use example MIDI files for interpolation endpoints.
        input_trio_midi_data = [
            tf.gfile.Open(fn, 'rb').read()
            for fn in sorted(tf.gfile.Glob('./VAE/midi/trio_16bar*.mid'))]

    elif alg == 'flat-trio_16bar':
        flat_trio_16bar_config = configs.CONFIG_MAP['flat-trio_16bar']
        config = flat_trio_16bar_config
        trio_models['baseline_flat_trio_16bar'] = TrainedModel(config, 
            batch_size=4, checkpoint_dir_or_path='./VAE/checkpoints/trio_16bar_flat.ckpt')
        
        #@title Option 1: Use example MIDI files for interpolation endpoints.
        input_trio_midi_data = [
            tf.gfile.Open(fn, 'rb').read()
            for fn in sorted(tf.gfile.Glob('./VAE/midi/trio_16bar*.mid'))]

    elif alg == 'cat-drums_2bar_small':
        drums_2bar_small_config = configs.CONFIG_MAP['cat-drums_2bar_small']
        config = drums_2bar_small_config
        trio_models['cat-drums_2bar_small'] = TrainedModel(config, 
            batch_size=4, checkpoint_dir_or_path='./VAE/checkpoints/drums_2bar_small.hikl.ckpt')
        input_trio_midi_data = [
            tf.gfile.Open(fn, 'rb').read()
            for fn in sorted(tf.gfile.Glob('./VAE/midi/drums_2bar*.mid'))]
    else:
        raise ValueError('Unrecognized Algorithm')

    return input_trio_midi_data, config, trio_models


#@title Option 1: Use example MIDI files for interpolation endpoints.

def generate(input_trio_midi_data, config):
    """
    given input midi files and alg config
    generate notes sequence
    """

    trio_input_seqs = [mm.midi_to_sequence_proto(m) for m in input_trio_midi_data]
    extracted_trios = []
    for ns in trio_input_seqs:
        extracted_trios.extend(
            config.data_converter.from_tensors(
              config.data_converter.to_tensors(ns)[1]))

    return extracted_trios

def interpolateFromInput(extracted_trios, trio_models, alg):
    """
    interpolate needs two files to play with
    given input 2 midi files/ config(trio_models)/ alg
    generate notesequences
    """
    #@title Compute the reconstructions and mean of the two trios, selected from the previous cell.
    trio_interp_model = alg #@param ["hierdec_trio_16bar", "baseline_flat_trio_16bar"]

    start_trio = 0 #@param {type:"integer"}
    end_trio = 1 #@param {type:"integer"}
    start_trio = extracted_trios[start_trio]
    end_trio = extracted_trios[end_trio]

    temperature = 0.5 #@param {type:"slider", min:0.1, max:1.5, step:0.1}
    trio_16bar_mean = interpolate(trio_models[trio_interp_model], start_trio, 
        end_trio, num_steps=3, max_length=256, individual_duration=32, temperature=temperature)     

    mm.midi_io.note_sequence_to_midi_file(trio_16bar_mean, './VAE/output/%s_mean.mid' % trio_interp_model)
    print('file wrote')


def run(alg):
	input_trio_midi_data, config, trio_models = set_config(alg)
	extracted_trios = generate(input_trio_midi_data, config)
	interpolateFromInput(extracted_trios, trio_models, alg)

run('cat-drums_2bar_small')