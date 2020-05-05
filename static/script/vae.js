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

function interpolate(midi1, midi2) {
  
  //Quantize for musicVAE model
  const upload1 = (mm.urlToNoteSequence(midi1)
                  .then(ns_val => note_seq1 = ns_val)
                  .then(vars => upload1_quant = mm.sequences.quantizeNoteSequence(note_seq1, 4)))
  const upload2 = (mm.urlToNoteSequence(midi2)
                  .then(ns_val => note_seq2 = ns_val)
                  .then(vars => upload2_quant = mm.sequences.quantizeNoteSequence(note_seq2, 4)))

  // mm.Player.tone.context.resume();  // enable audio
  music_vae
  .interpolate([upload1_quant, upload2_quant], 4)
  .then((sample) => {
    const concatenated = mm.sequences.concatenate(sample);
    vaePlayer.start(concatenated);
  });

  if (vaePlayer.isPlaying()) {

    vaePlayer.stop();
    return;
  }
}

function first(midi1, midi2){

  interpolate(midi1, midi2);
  setTimeout(() => {  interpolate(midi1, midi2); }, 2000);
  
}