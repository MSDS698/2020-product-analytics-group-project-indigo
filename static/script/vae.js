// Initialize the model.
const music_vae = new mm.MusicVAE('https://storage.googleapis.com/magentadata/js/checkpoints/music_vae/mel_4bar_small_q2');


// Create a player to play the sampled sequence.
let vaeViz;
const vaePlayer = new mm.SoundFontPlayer('https://storage.googleapis.com/magentadata/js/soundfonts/sgm_plus');
const vae_temperature = 1.5

const config = {
    noteHeight: 6,
    pixelsPerTimeStep: 60,  // like a note width
    noteSpacing: 1,
    noteRGB:'223,66,98',
    activeNoteRGB:'157, 229, 184',

}

let upload1_quant;
let upload2_quant;
let note_seq1;
let note_seq2;
let concatenated;
let unquantized;

//download
let output_midi;
let output_file;
//saving
let output_filename;
let json_data;

init();

$(".noUi-touch-area").click(function(){
    console.log('HI')
});

function init(midi1, midi2) {
    vaePlayer.callbackObject = {
        run: (note) => vaeViz.redraw(note, true),
        stop: () => {}
    };

    music_vae.initialize()
    .then(function(){
        mm.urlToNoteSequence(midi1)
        .then(ns_val1 => note_seq1 = ns_val1)
        .then(vars => upload1_quant = mm.sequences.quantizeNoteSequence(note_seq1, 4))
        .then(vars => mm.urlToNoteSequence(midi2))
        .then(ns_val2 => note_seq2 = ns_val2)
        .then(vars => upload2_quant = mm.sequences.quantizeNoteSequence(note_seq2, 4))
        .then(vars => music_vae
          .interpolate([upload1_quant, upload2_quant], 4)
          .then((sample) => {
            concatenated = mm.sequences.concatenate(sample);
            concatenated['tempos'][0]['qpm'] = 80;
            concatenated['tempos'][0]['time'] = 0;
            unquantized = mm.sequences.unquantizeSequence(concatenated);
            document.getElementById('loading').style.display = 'none';
            vaeViz = new mm.PianoRollSVGVisualizer(
                            unquantized,
                            document.getElementById('vaeViz'),
                            config
                            );
            $("#slider").css("width", "2880px");
            $("#sample").show();
            $("#play").show();
            $("#saveDiv").show();
            }));
  });
}

function start_stop(){
  if (vaePlayer.isPlaying()) {
    vaePlayer.stop();
  }
  else{
    vaePlayer.start(concatenated);
  }
}

function save(){
    output_filename = $("#save_name").val();
    if(output_filename==''){
        alert("Filename can't be empty, please enter a valid filename");
        return
    }
    json_data = {"noteSequence": mm.sequences.unquantizeSequence(concatenated),
                 "output_filename":output_filename,
                 "model": "vae"
                }
    $.ajax({
        url: "/save",
        method: "POST",
        contentType: 'application/json',
        data: JSON.stringify(json_data),
        success: function(result){
            alert(result);
        },
        error: function(jqXHR, textStatus, errorThrown){
            alert("Error: "+errorThrown);
        }
    });
}

// Credit to: https://codepen.io/iansimon/embed/Bxgbgz
function download(){
  output_filename = $("#save_name").val();
  output_midi = mm.sequenceProtoToMidi(concatenated); // produces a byteArray
  output_file = new Blob([output_midi], {type: 'audio/midi'});

  if (window.navigator.msSaveOrOpenBlob) {
    window.navigator.msSaveOrOpenBlob(file, 'output.mid');
  } else { // Others
    const a = document.createElement('a');
    const url = URL.createObjectURL(output_file);
    a.href = url;
    a.download = output_filename+'.mid';
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    }, 0);
  }
}


function modifyInstrument(obj){
    var program = parseInt(obj.options[obj.selectedIndex].value);
    concatenated['notes'].forEach(note => note['program']=program);
}

function trim(){
    concatenated = mm.sequences.trim(concatenated,64,128);
    concatenated['totalTime'] = 12;
    unquantized = mm.sequences.unquantizeSequence(concatenated);
    vaeViz = new mm.PianoRollSVGVisualizer(
                            unquantized,
                            document.getElementById('vaeViz'),
                            config
                            );
    $("#slider").css("width", "800px");
    $("#vaeViz").css("width", "800px");
    $("#slider").css("margin-left","220px");
}