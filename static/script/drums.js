const config = {
    noteHeight: 6,
    pixelsPerTimeStep: 60,  // like a note width
    noteSpacing: 1,
    noteRGB:'223,66,98',
    activeNoteRGB:'157, 229, 184',

}

// Array to hold PianoRollSVGVisualizer objects (one for original track, one for added drum layer)
let sampleViz;
let instrumentViz;
let drumsViz;

// MIDI Players
let samplePlayer;
let instrumentPlayer;
let drumsPlayer
let combinedPlayer;

//note sequences
let note_seq;
let quantized_note_seq;
let separated_sequences;
let instrument_seq;
let generated_seq;
let combined_seq;
let generated_unquantized;
let instrument_unquantized;

//tempos
let sample_tempo;

// programs in midi file
let programs;
let program_notes;

// models
let music_rnn;

init();

function init(){
    drums_rnn = new mm.MusicRNN('https://storage.googleapis.com/magentadata/js/checkpoints/music_rnn/drum_kit_rnn');
    drums_rnn.initialize()
    .then(function(){
        $("#drum_rnn").show();
    });

    samplePlayer = new mm.SoundFontPlayer('https://storage.googleapis.com/magentadata/js/soundfonts/sgm_plus');
    instrumentPlayer = new mm.SoundFontPlayer('https://storage.googleapis.com/magentadata/js/soundfonts/sgm_plus');
    drumsPlayer = new mm.SoundFontPlayer('https://storage.googleapis.com/magentadata/js/soundfonts/sgm_plus');
    combinedPlayer = new mm.SoundFontPlayer('https://storage.googleapis.com/magentadata/js/soundfonts/sgm_plus');

    samplePlayer.callbackObject = {
        run: (note) => sampleViz.redraw(note, true),
        stop: () => {}
    };
    instrumentPlayer.callbackObject = {
        run: (note) => instrumentViz.redraw(note, true),
        stop: () => {}
    };
    drumsPlayer.callbackObject = {
        run: (note) => drumsViz.redraw(note, true),
        stop: () => {}
    };
    combinedPlayer.callbackObject = {
        run: function(note){
            drumsViz.redraw(note, true);
            sampleViz.redraw(note, true);
            instrumentViz.redraw(note, true);
            },
        stop: () => {}
    };

}

// Event Listeners
$('#samples').on('change', function () {
    mm.urlToNoteSequence('/static/guitar_bass_samples/'+this.value)
    .then(ns_val => note_seq = ns_val)
    .then(vars => quantized_note_seq = mm.sequences.quantizeNoteSequence(note_seq, 4))
    .then(function(){
        $("#sample").show();
        sample_tempo = note_seq['tempos'];
        sampleViz = new mm.PianoRollSVGVisualizer(
                                note_seq,
                                document.getElementById('sampleViz'),
                                config
                                );
    })
    .then(function(){
        // Find the programs/instruments that exist in the MIDI file
        programs = [...new Set(quantized_note_seq['notes'].map(note => note.program))];
        // Create an array of arrays, one array for each program/instrument's notes
        program_notes = programs.map(program => notes_filter(program));
        // Create array of Magenta note_sequence objects, one fore each program/instrument
        separated_sequences =  program_notes.map(obj => replace_notes_in_sequence(quantized_note_seq, obj));
    })
    .then(function(){
        if (separated_sequences.length > 1) {
            // call function to load list showing option for track separately
            create_instrument_list(separated_sequences);
            $("#instrumentList").show();
        }
        else {
             alert("Only one instrument found in MIDI file, click ok to continue");
             instrument_seq = quantized_note_seq;
        }

    })

});

$('#instruments').on('change', function () {
    console.log(this.value)
    instrument_seq = separated_sequences.filter((val) => val['instrument']==this.value)[0]['trimmed_seq'];
    instrument_unquantized = mm.sequences.unquantizeSequence(instrument_seq);
    instrumentViz = new mm.PianoRollSVGVisualizer(
                                instrument_unquantized,
                                document.getElementById('instrumentViz'),
                                config
                                );
    $("#instrument").show();
});

$("#drums_rnn").click(function(){
    let temp = parseFloat($("#rnn_temp").val())
    console.log(temp);
    steps = quantized_note_seq["totalQuantizedSteps"];

    drums_rnn.continueSequence(instrument_seq, steps, temp)
    .then(function(sample) {
        generated_seq = sample;
        generated_seq['tempos'] = sample_tempo;
        $("#drums").show();
        generated_unquantized = mm.sequences.unquantizeSequence(generated_seq);
        drumsViz = new mm.PianoRollSVGVisualizer(
                                generated_unquantized,
                                document.getElementById('drumsViz'),
                                config
                              );
        combined_seq = mm.sequences.clone(quantized_note_seq);
        combined_seq['notes'].push(...generated_seq['notes']);

        $("#combined").show();
    })
});

$("#btnPlayCombined").click(function(){
    combinedPlayer.start(combined_seq);
    $("#stopCombined").show();
});

$("#stopCombined").click(function(){
    combinedPlayer.stop();
});

$("#btnPlaySample").click( (e) => play(samplePlayer, note_seq));
$("#btnPlayDrums").click( (e) => play(drumsPlayer, generated_seq));
$("#btnPlayInstrument").click( (e) => play(instrumentPlayer, instrument_seq));


function play(player, n_seq){
    if (player.isPlaying()) {
        player.stop();
      } else {
        player.start(n_seq);
      }
}


function notes_filter(program){
    /**
    Given note-sequence for entire MIDI file, filter to just notes for one program (instrument)
    Part of functionality to split out original MIDI file into separate instruments
    */
    filtered_notes = quantized_note_seq['notes'].filter(
        function (note) {
            return note.program == program;
        }
    )
    // Calculate min/max steps in notes, to create a trimmed version of it (no starting/ending silence)
    min_step = Math.min.apply(null, filtered_notes.map(note => note['quantizedStartStep']));
    max_step = Math.max.apply(null, filtered_notes.map(note => note['quantizedEndStep']));


    return {"program":program, "notes":filtered_notes, "min_step":min_step, "max_step":max_step}
}


function replace_notes_in_sequence(sequence, obj){
    /**
    Replace notes of a given sequence with new value, tag returned object with the name of the instrument
    Basically recreates the original note_sequence object, but just with the notes from a single program/instrument
    */
    seq_clone = mm.sequences.clone(sequence)
    seq_clone['notes'] = obj["notes"]
    trimmed_seq = mm.sequences.trim(seq_clone, obj['min_step'], obj['max_step'])
    return {"sequence":seq_clone, "trimmed_seq":trimmed_seq, "program":obj["program"], "instrument":instrument_mappings[obj["program"]]}


}


function add_instrument_option(sequence, index, array){
  $("#instruments").append("<option value='"+sequence['instrument']+"'>"+sequence['instrument']+"</option>");
}

// Create UI for separate instruments
function create_instrument_list(sequences){
    sequences.forEach(add_instrument_option);
}



