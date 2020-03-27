function initialize_player(){
  const player = new mm.SoundFontPlayer('https://storage.googleapis.com/magentadata/js/soundfonts/sgm_plus');
  return player

}

// Given note-sequence for entire MIDI file, filter to just notes for one program (instrument)
function notes_filter(program){
  filtered_notes =  quant_note_seq['notes'].filter(
    function (note) {
        return note.program == program;
    }
  )
  // Calculate min/max steps in notes, to create a trimmed version of it (no starting/ending silence)
  min_step = Math.min.apply(null, filtered_notes.map(note => note['quantizedStartStep']));
  max_step = Math.max.apply(null, filtered_notes.map(note => note['quantizedEndStep']));


  return {"program":program, "notes":filtered_notes, "min_step":min_step, "max_step":max_step}
}

// Replace notes of a given sequence with new value, tag returned object with the name of the instrument
function replace_notes_in_sequence(sequence, obj){
  seq_clone = mm.sequences.clone(sequence)
  seq_clone['notes'] = obj["notes"]
  trim_seq = mm.sequences.trim(seq_clone, obj['min_step'], obj['max_step'])
  return {"sequence":seq_clone, "trimmed_sequence":trim_seq, "program":obj["program"], "instrument":instrument_mappings[obj["program"]]} 
}

// Format element to be appended
function format_track(sequence, index, array){
  $("#tracks").append("<h3>"+sequence['instrument']+"</h3>");
  $("#tracks").append("<input type='image' src='static/playbutton.png' height='30px' width='30px' onclick='player.start(separated_sequences["+index+"][\"trimmed_sequence\"])'/>")
}

// Create UI for separate tracks
function add_tracks(sequences){
  sequences.forEach(format_track);
}

//
function load_midi_sample(){
  // Load midi from url and chain operations to create note-sequence, quantize, and show play button
  mm.urlToNoteSequence('https://bitmidi.com/uploads/17583.mid')
            .then(ns_val => note_seq = ns_val)
            .then(unimportant => quant_note_seq = mm.sequences.quantizeNoteSequence(note_seq, 4))
            .then(function(){$("#playbutton").show()})
            .then(function(){
              const programs = [...new Set(quant_note_seq['notes'].map(note => note.program))];
  
              program_notes = programs.map(program => notes_filter(program));

              separated_sequences =  program_notes.map(obj => replace_notes_in_sequence(quant_note_seq, obj));


            })
            .then(function(){
              // call function to load UI showing each track separately
              add_tracks(separated_sequences);
            })          
  
  music_rnn = new mm.MusicRNN('https://storage.googleapis.com/magentadata/js/checkpoints/music_rnn/melody_rnn');
  // Only give users ability to run sample through model AFTER model has finished initializing
  music_rnn.initialize()
    .then(function(){$("#rnn").show()});
  music_vae = new mm.MusicVAE('https://storage.googleapis.com/magentadata/js/checkpoints/music_vae/mel_4bar_small_q2');
  music_vae.initialize()
    .then(function(){$("#vae").show()});

}

// try using mostly jquery to handle DOM manipulation
$("#loadmidi").click(function(){
  load_midi_sample();
});

$("#playbutton").click(function(){
  player.start(note_seq);
  $("#stopbutton").show()
});

$("#stopbutton").click(function(){
  player.stop()
});

$("#rnnsample").click(function(){
  let rnn_steps = parseInt($("#rnn_steps").val())
  let rnn_temp = parseInt($("#rnn_temp").val())

  let trim_note_seq = mm.sequences.trim(quant_note_seq, 0, 300);
  music_rnn.continueSequence(trim_note_seq, rnn_steps, rnn_temp)
    .then(sample => player.start(sample));
});

$("#vaesample").click(function(){
  let vae_temperature = parseInt($("#vae_temp").val())
  
  let trim_note_seq = mm.sequences.trim(quant_note_seq, 0, 300);
  music_vae.sample(1, vae_temperature)
    .then(sample => player.start(sample[0]));
});


// First thing page does is intialize player, but how do I know player is ready when user clicks button?
// This seems janky and like there should be a better way to start player
const player = initialize_player()