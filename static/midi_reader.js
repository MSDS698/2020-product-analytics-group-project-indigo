// Array to hold PianoRollSVGVisualizer objects (one for each track)
let noteCanvases = [];
// Array to hold music players (one for each track) (Not used yet, currently still just using one main player)
let players = [];

// Original Complete Midi File
const main_player = initialize_player();

//note sequences
let note_seq;
let quant_note_seq;
let separated_sequences;

// programs in midi file
let programs;
let program_notes;

// models
let music_rnn;
let music_vae;

///////////////////////////////////

var Player = {

    buffer: null,

    duration: 0,

    tracks: [
        {
            artist: "",
            song: "",
            url: "http://"+"katiebaca.com/tutorial/odd-look.mp3"
        }
    ],

    init: function () {
        window.AudioContext = window.AudioContext || window.webkitAudioContext;
        this.context = new AudioContext();
        this.context.suspend && this.context.suspend();
        this.firstLaunch = true;
        try {
            this.javascriptNode = this.context.createScriptProcessor(2048, 1, 1);
            this.javascriptNode.connect(this.context.destination);
            this.analyser = this.context.createAnalyser();
            this.analyser.connect(this.javascriptNode);
            this.analyser.smoothingTimeConstant = 0.6;
            this.analyser.fftSize = 2048;
            this.source = this.context.createBufferSource();
            this.destination = this.context.destination;
            this.loadTrack(0);

            this.gainNode = this.context.createGain();
            this.source.connect(this.gainNode);
            this.gainNode.connect(this.analyser);
            this.gainNode.connect(this.destination);

            this.initHandlers();
        } catch (e) {
            Framer.setLoadingPercent(1);
        }
        Framer.setLoadingPercent(1);
        Scene.init();
    },

    loadTrack: function (index) {
        var that = this;
        var request = new XMLHttpRequest();
        var track = this.tracks[index];
        document.querySelector('.song .artist').textContent = track.artist;
        document.querySelector('.song .name').textContent = track.song;
        this.currentSongIndex = index;

        request.open('GET', track.url, true);
        request.responseType = 'arraybuffer';

        request.onload = function() {
            that.context.decodeAudioData(request.response, function(buffer) {
                that.source.buffer = buffer;
            });
        };

        request.send();
    },

    nextTrack: function () {
        return;
        ++this.currentSongIndex;
        if (this.currentSongIndex == this.tracks.length) {
            this.currentSongIndex = 0;
        }

        this.loadTrack(this.currentSongIndex);
    },

    prevTrack: function () {
        return;
        --this.currentSongIndex;
        if (this.currentSongIndex == -1) {
            this.currentSongIndex = this.tracks.length - 1;
        }

        this.loadTrack(this.currentSongIndex);
    },

    play: function () {
        this.context.resume && this.context.resume();
        if (this.firstLaunch) {
            this.source.start();
            this.firstLaunch = false;
        }
    },

    stop: function () {
        this.context.currentTime = 0;
        this.context.suspend();
    },

    pause: function () {
        this.context.suspend();
    },

    mute: function () {
        this.gainNode.gain.value = 0;
    },

    unmute: function () {
        this.gainNode.gain.value = 1;
    },

    initHandlers: function () {
        var that = this;

        this.javascriptNode.onaudioprocess = function() {
            Framer.frequencyData = new Uint8Array(that.analyser.frequencyBinCount);
            that.analyser.getByteFrequencyData(Framer.frequencyData);
        };
    }
};

///////////////

function initialize_player(){
  // Use soundfount to be able to play different instruments (not just piano)
  const player = new mm.SoundFontPlayer('https://storage.googleapis.com/magentadata/js/soundfonts/sgm_plus');
  return player

}

// Given note-sequence for entire MIDI file, filter to just notes for one program (instrument)
// Part of functionality to split out original MIDI file into separate instruments
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
// Basically recreates the original note_sequence object, but just with the notes from a single program/instrument
function replace_notes_in_sequence(sequence, obj){
  seq_clone = mm.sequences.clone(sequence)
  seq_clone['notes'] = obj["notes"]
  trim_seq = mm.sequences.trim(seq_clone, obj['min_step'], obj['max_step'])
  return {"sequence":seq_clone, "trimmed_sequence":trim_seq, "program":obj["program"], "instrument":instrument_mappings[obj["program"]]}
}

// Format element to be appended
function format_track(sequence, index, array){
  $("#tracks").append("<h3>"+sequence['instrument']+"</h3>");
  // Add new player to control this track (mainly so callback/draw can be controlled on individual tracks). Not yet in use
  players.push(initialize_player);
  $("#tracks").append("<input type='image' src='static/playbutton.png' height='30px' width='30px' onclick='main_player.start(separated_sequences["+index+"][\"trimmed_sequence\"])'/>");
  $("#tracks").append("<input type='image' src='static/stopbutton.png' height='30px' width='30px' onclick='main_player.stop()'/>");
  // SVG element holds the visualized note image
  $("#tracks").append("<div style='overflow:scroll;'><svg id='noteCanvas"+index+"'></svg></div>");

  noteCanvases.push(new mm.PianoRollSVGVisualizer(
    separated_sequences[index]['trimmed_sequence'], document.getElementById('noteCanvas'+index),
    {noteRGB:'223,66,98', activeNoteRGB:'157, 229, 184', noteHeight:5}));

}

// Create UI for separate tracks
function add_tracks(sequences){
  sequences.forEach(format_track);
}

// Main function, kicks everything else off
function load_midi_sample(){
  // Load midi from url and chain operations to create note-sequence, quantize, and show play button
  mm.urlToNoteSequence('https://bitmidi.com/uploads/17583.mid')
            .then(ns_val => note_seq = ns_val)
            .then(unimportant => quant_note_seq = mm.sequences.quantizeNoteSequence(note_seq, 4))
            .then(function(){$("#playbutton").show()})
            .then(function(){
              // Find the programs/instruments that exist in the MIDI file
              programs = [...new Set(quant_note_seq['notes'].map(note => note.program))];
              // Create an array of arrays, one array for each program/instrument's notes
              program_notes = programs.map(program => notes_filter(program));
              // Create array of Magenta note_sequence objects, one fore each program/instrument
              separated_sequences =  program_notes.map(obj => replace_notes_in_sequence(quant_note_seq, obj));


            })
            .then(function(){
              // call function to load UI showing each track separately
              add_tracks(separated_sequences);
            })

  // Load models
  music_rnn = new mm.MusicRNN('https://storage.googleapis.com/magentadata/js/checkpoints/music_rnn/melody_rnn');
  // Only give users ability to run sample through model AFTER model has finished initializing
  music_rnn.initialize()
    .then(function(){$("#rnn").show()});
  music_vae = new mm.MusicVAE('https://storage.googleapis.com/magentadata/js/checkpoints/music_vae/mel_4bar_small_q2');
  music_vae.initialize()
    .then(function(){$("#vae").show()});

}

// Event Listeners
$("#loadmidi").click(function(){
  load_midi_sample();
});

$("#playbutton").click(function(){
  main_player.start(note_seq);
  $("#stopbutton").show()
});

$("#stopbutton").click(function(){
  main_player.stop()
});

$("#rnnsample").click(function(){
  let rnn_steps = parseInt($("#rnn_steps").val())
  let rnn_temp = parseInt($("#rnn_temp").val())

  let trim_note_seq = mm.sequences.trim(quant_note_seq, 0, 300);
  music_rnn.continueSequence(trim_note_seq, rnn_steps, rnn_temp)
    .then(sample => main_player.start(sample));
});

$("#vaesample").click(function(){
  let vae_temperature = parseInt($("#vae_temp").val())

  let trim_note_seq = mm.sequences.trim(quant_note_seq, 0, 300);
  music_vae.sample(1, vae_temperature)
    .then(sample => main_player.start(sample[0]));
});