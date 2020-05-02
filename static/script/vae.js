// Initialize the model.
const music_vae = new mm.MusicVAE('https://storage.googleapis.com/magentadata/js/checkpoints/music_vae/mel_4bar_small_q2');

music_vae.initialize().then(() => {
  document.getElementById('loading').style.display = 'none';
  [...document.getElementsByTagName('button')].forEach(b => b.style = '');
});

let note_seq;
let quantized_note_seq;

// Create a player to play the sampled sequence.
const vaePlayer = new mm.Player();
const vae_temperature = 1.5
const biggie = (mm.urlToNoteSequence('../static/bass_4bars.mid')
                .then(ns_val => note_seq = ns_val)
                .then(vars => quantized_note_seq = mm.sequences.quantizeNoteSequence(note_seq, 4)))

// const mid1 = fs.readFileSync('midi/biggie_notorious_thugs.mid');
// const ns1 = midi_io.midiToSequenceProto(mid1);

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

let combined;

function vae_interpolate() {
  mm.Player.tone.context.resume();  // enable audio
  if (vaePlayer.isPlaying()) {
    vaePlayer.stop();
    return;
}

  // Music VAE requires quantized melodies, so quantize them first.
  const star = mm.sequences.quantizeNoteSequence(TWINKLE_TWINKLE, 4);
  // music_vae.interpolate([star, LITTLE_TEAPOT], 4).then((sample) => {combined = sample[1]; vaePlayer.start(combined)})
  music_vae
  .interpolate([biggie, LITTLE_TEAPOT], 4)
  .then((sample) => {
    const concatenated = mm.sequences.concatenate(sample);
    // const concatenated = concatenateSequences(sample);
    vaePlayer.start(concatenated);
  });
}

// function concatenateSequences(seqs) {
//   const seq = mm.sequences.clone(seqs[0]);
//   let numSteps = seqs[0].totalQuantizedSteps;
//   for (let i=1; i<seqs.length; i++) {
//     const s = mm.sequences.clone(seqs[i]);
//     s.notes.forEach(note => {
//       note.quantizedStartStep += numSteps;
//       note.quantizedEndStep += numSteps;
//       seq.notes.push(note);
//     });
//     numSteps += s.totalQuantizedSteps;
//   }
//   seq.totalQuantizedSteps = numSteps;
//   return seq;
// }
