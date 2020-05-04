// Initialize the model.
const music_vae = new mm.MusicVAE('https://storage.googleapis.com/magentadata/js/checkpoints/music_vae/mel_4bar_small_q2');
music_vae.initialize().then(() => {
  document.getElementById('loading').style.display = 'none';
  [...document.getElementsByTagName('button')].forEach(b => b.style = '');
});

// Create a player to play the sampled sequence.
const vaePlayer = new mm.Player();
const vae_temperature = 1.5

let note_seq;
let quantized_note_seq;
// const upload1 = (mm.urlToNoteSequence('../static/guitar_bass_samples/bass_4bars.mid')
//                 .then(ns_val => note_seq = ns_val)
//                 .then(vars => upload1_quant = mm.sequences.quantizeNoteSequence(note_seq, 4)))
// const upload2 = (mm.urlToNoteSequence('../static/midi_samples/biggie_notorious_thugs.mid')
//                 .then(ns_val => note_seq = ns_val)
//                 .then(vars => upload2_quant = mm.sequences.quantizeNoteSequence(note_seq, 4)))

const TWINKLE_TWINKLE = {
  notes: [
    {pitch: 60, startTime: 0.0, endTime: 0.5},
    {pitch: 60, startTime: 0.5, endTime: 1.0},
    {pitch: 67, startTime: 1.0, endTime: 1.5},
    {pitch: 67, startTime: 1.5, endTime: 2.0},
    {pitch: 69, startTime: 2.0, endTime: 2.5},
    {pitch: 69, startTime: 2.5, endTime: 3.0},
    {pitch: 67, startTime: 3.0, endTime: 4.0},
    {pitch: 65, startTime: 4.0, endTime: 4.5},
    {pitch: 65, startTime: 4.5, endTime: 5.0},
    {pitch: 64, startTime: 5.0, endTime: 5.5},
    {pitch: 64, startTime: 5.5, endTime: 6.0},
    {pitch: 62, startTime: 6.0, endTime: 6.5},
    {pitch: 62, startTime: 6.5, endTime: 7.0},
    {pitch: 60, startTime: 7.0, endTime: 8.0},  
  ],
  totalTime: 8
};

const LITTLE_TEAPOT = {
    notes: [
      { pitch: 69, quantizedStartStep: 0, quantizedEndStep: 2, program: 0 },
      { pitch: 71, quantizedStartStep: 2, quantizedEndStep: 4, program: 0 },
      { pitch: 73, quantizedStartStep: 4, quantizedEndStep: 6, program: 0 },
      { pitch: 74, quantizedStartStep: 6, quantizedEndStep: 8, program: 0 },
      { pitch: 76, quantizedStartStep: 8, quantizedEndStep: 10, program: 0 },
      { pitch: 81, quantizedStartStep: 12, quantizedEndStep: 16, program: 0 },
      { pitch: 78, quantizedStartStep: 16, quantizedEndStep: 20, program: 0 },
      { pitch: 81, quantizedStartStep: 20, quantizedEndStep: 24, program: 0 },
      { pitch: 76, quantizedStartStep: 24, quantizedEndStep: 26, program: 0 }
    ],
    quantizationInfo: { stepsPerQuarter: 4 },
    totalQuantizedSteps: 26,
  };

// function interpolate() {
function interpolate(midi1, midi2) {

  console.log(typeof midi1, midi1)
  console.log(typeof midi2, midi2)

  mm.urlToNoteSequence(midi1)  

  // var upload1 = (mm.urlToNoteSequence(midi1)
  //                 .then(ns_val => note_seq = ns_val)
  //                 .then(vars => upload1_quant = mm.sequences.quantizeNoteSequence(note_seq, 4)))
  // var upload2 = (mm.urlToNoteSequence(midi2)
  //                 .then(ns_val => note_seq = ns_val)
  //                 .then(vars => upload2_quant = mm.sequences.quantizeNoteSequence(note_seq, 4)))

  mm.Player.tone.context.resume();  // enable audio
  if (vaePlayer.isPlaying()) {
    vaePlayer.stop();
    return;
  }

  // Music VAE requires quantized melodies, so quantize them first.
  // const star = mm.sequences.quantizeNoteSequence(TWINKLE_TWINKLE, 4);
  music_vae
  .interpolate([upload1_quant, upload2_quant], 4)
  .then((sample) => {
    const concatenated = mm.sequences.concatenate(sample);
    vaePlayer.start(concatenated);
  });
}