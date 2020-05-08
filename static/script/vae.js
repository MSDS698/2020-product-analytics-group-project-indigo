// Initialize the model.
const music_vae = new mm.MusicVAE('https://storage.googleapis.com/magentadata/js/checkpoints/music_vae/mel_4bar_small_q2');
music_vae.initialize().then(() => {
  document.getElementById('loading').style.display = 'none';
  [...document.getElementsByTagName('button')].forEach(b => b.style = '');
});

// Create a player to play the sampled sequence.
const vaePlayer = new mm.Player();
const vae_temperature = 1.5

let upload1_quant;
let upload2_quant;
let note_seq1;
let note_seq2;
let concatenated

//download
let output_midi;
let output_file;
//saving
let output_filename;
let json_data;

function interpolate(midi1, midi2) {
  
  //Quantize note sequences and pass note sequences to interpolate function of MusicVAE
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
                        vaePlayer.start(concatenated);
                        $("#saveDiv").show();
                      }));
}

function stop(){
  if (vaePlayer.isPlaying()) {
    vaePlayer.stop();
  }
  else{
    vaePlayer.start();
  }
}

function save(){
    output_filename = $("#save_name").val();
    if(output_filename==''){
        alert("Filename can't be empty, please enter a valid filename");
        return
    }
    json_data = {"byteArray": mm.sequenceProtoToMidi(mm.sequences.unquantizeSequence(concatenated)),
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