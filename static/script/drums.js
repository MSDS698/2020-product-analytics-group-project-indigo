// Array to hold PianoRollSVGVisualizer objects (one for original track, one for added drum layer)
let noteCanvases = {};
// Array to hold music players (one for each track) (Not used yet, currently still just using one main player)
let players = [];

const config = {
    noteHeight: 6,
    pixelsPerTimeStep: 60,  // like a note width
    noteSpacing: 1,
    noteRGB:'223,66,98',
    activeNoteRGB:'157, 229, 184',

}
// Original Complete Midi File
const main_player = initialize_player();
let combined_player;

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


function initialize_player(){
  // Use soundfount to be able to play different instruments (not just piano)
  const player = new mm.SoundFontPlayer('https://storage.googleapis.com/magentadata/js/soundfonts/sgm_plus');
  return player
}


// Even Listeners
$('#samples').on('change', function () {
    mm.urlToNoteSequence('/static/guitar_bass_samples/'+this.value)
    .then(ns_val => note_seq = ns_val)
    .then(unimportant => quant_note_seq = mm.sequences.quantizeNoteSequence(note_seq, 4))
    .then(function(){
        $("#svg1").show();
        noteCanvases['user'] = new mm.PianoRollSVGVisualizer(
                                note_seq,
                                document.getElementById('originalSVG'),
                                config
                                );
    });


    drums_rnn = new mm.MusicRNN('https://storage.googleapis.com/magentadata/js/checkpoints/music_rnn/drum_kit_rnn');
    drums_rnn.initialize()
    .then(function(){
        $("#div2").show();
    });

});

$("#drums_rnn").click(function(){
    let temp = parseFloat($("#rnn_temp").val())
    console.log(temp);
    steps = quant_note_seq["totalQuantizedSteps"];

    drums_rnn.continueSequence(quant_note_seq, steps, temp)
    .then(function(sample) {
        generated_seq = sample;
        $("#svg2").show();
        unquant_note_seq = mm.sequences.unquantizeSequence(generated_seq);
        noteCanvases['drums'] = new mm.PianoRollSVGVisualizer(
                                unquant_note_seq,
                                document.getElementById('drumsSVG'),
                                config
                              );
        combined_seq = mm.sequences.clone(quant_note_seq);
        combined_seq['notes'].push(...generated_seq['notes']);

        combined_player = new mm.SoundFontPlayer('https://storage.googleapis.com/magentadata/js/soundfonts/sgm_plus');
        combined_player.callbackObject = {
            run: function(note){
                noteCanvases['drums'].redraw(note, true);
                noteCanvases['user'].redraw(note, true);
            },
            stop: () => {console.log('done')}
        };

        $("#combined").show();
    })
});

$("#combined").click(function(){
    combined_player.start(combined_seq);
    $("#stopbutton").show();
});

$("#stopbutton").click(function(){
    combined_player.stop()
});




