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
let quant_note_seq;
let separated_sequences;
let generated_seq;
let combined_seq;

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
            },
        stop: () => {}
    };

}

// Even Listeners
$('#samples').on('change', function () {
    mm.urlToNoteSequence('/static/guitar_bass_samples/'+this.value)
    .then(ns_val => note_seq = ns_val)
    .then(unimportant => quant_note_seq = mm.sequences.quantizeNoteSequence(note_seq, 4))
    .then(function(){
        $("#sample").show();
        sampleViz = new mm.PianoRollSVGVisualizer(
                                note_seq,
                                document.getElementById('sampleViz'),
                                config
                                );
    });

});

$("#drums_rnn").click(function(){
    let temp = parseFloat($("#rnn_temp").val())
    console.log(temp);
    steps = quant_note_seq["totalQuantizedSteps"];

    drums_rnn.continueSequence(quant_note_seq, steps, temp)
    .then(function(sample) {
        generated_seq = sample;
        $("#drums").show();
        unquant_note_seq = mm.sequences.unquantizeSequence(generated_seq);
        drumsViz = new mm.PianoRollSVGVisualizer(
                                unquant_note_seq,
                                document.getElementById('drumsViz'),
                                config
                              );
        combined_seq = mm.sequences.clone(quant_note_seq);
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

function play(player, n_seq){
    if (player.isPlaying()) {
        player.stop();
      } else {
        player.start(n_seq);
      }
}




