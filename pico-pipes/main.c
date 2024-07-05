#include "main.h"

////////////////////////////////////////////// Helpers /////////////////////////////////////////////

/**
 * Get milliseconds since boot
 */
uint64_t get_ms_now() {
  uint64_t now_us = to_us_since_boot(get_absolute_time());
  return now_us / 1000;
};

/**
 * Get frequency for a given MIDI pitch value.
 */
float pitch_get_freq(int pitch) {
  return (pitch > PITCH_TABLE_SIZE) ? 1 : pitch_table[pitch];
};

////////////////////////////////////////////// Notes ///////////////////////////////////////////////

struct Note {
  int track;
  int pitch;
  float on_at;
  float off_at;
};

/**
 * Create Note structure.
 */
struct Note note_create(const float *row) {
  struct Note n;
  n.track = row[0];
  n.pitch = row[1];
  n.on_at = row[2];
  n.off_at = row[3];

  return n;
};

////////////////////////////////////////////// Motors //////////////////////////////////////////////

struct Motor {
  int pin;
  int is_on;
  uint64_t last_step_us;
  uint64_t step_delay_us;
  uint64_t note_start_us;
  uint64_t note_duration_ms;
};

/**
 * Setup a Motor data structure.
 */
struct Motor motor_create(int pin) {
  struct Motor m;
  m.pin = pin;
  m.is_on = FALSE;
  m.last_step_us = 0;
  m.step_delay_us = 0;
  m.note_start_us = 0;
  m.note_duration_ms = 0;

  // GPIO init
  gpio_init(pin);
  gpio_set_dir(pin, GPIO_OUT);

  return m;
};

/**
 * Update a motor with a new note event.
 */
void motor_set_note(struct Motor *m, struct Note n) {
  m->is_on = TRUE;

  // Duration control
  m->note_start_us = to_us_since_boot(get_absolute_time());
  m->note_duration_ms = (n.off_at - n.on_at) * 1000;

  // Set delay from pitch frequency
  m->step_delay_us = 1000000 / pitch_get_freq(n.pitch);
};

/**
 * Tick a motor.
 */
void motor_tick(struct Motor *m) {
  uint64_t now_us = to_us_since_boot(get_absolute_time());

  // Turn off?
  if (now_us - m->note_start_us > (m->note_duration_ms * 1000)) {
    m->is_on = FALSE;
  }

  // Take a step if step delay elapsed
  if (now_us - m->last_step_us > m->step_delay_us) {
    m->last_step_us = now_us;

    if (m->is_on == TRUE) {
      gpio_put(m->pin, 1);
      sleep_us(5);
      gpio_put(m->pin, 0);
    }
  }
};

//////////////////////////////////////////// Main loop /////////////////////////////////////////////

const int MOTOR_1_PIN = 5;
const int MOTOR_2_PIN = 4;
const int MOTOR_3_PIN = 3;
const int MOTOR_4_PIN = 2;

/**
 * Entry point.
 */
int main() {
  // Create motors
  struct Motor motor1 = motor_create(MOTOR_1_PIN);
  struct Motor motor2 = motor_create(MOTOR_2_PIN);
  struct Motor motor3 = motor_create(MOTOR_3_PIN);
  struct Motor motor4 = motor_create(MOTOR_4_PIN);

  // Pre-load first note
  int note_index = 0;
  struct Note next_note = note_create(NOTE_TABLE[note_index]);

  while (true) {
    motor_tick(&motor1);
    motor_tick(&motor2);
    motor_tick(&motor3);
    motor_tick(&motor4);

    // End?
    if (note_index == NUM_NOTES - 1) return 0;

    // Update next event
    if (get_ms_now() > next_note.on_at * 1000) {
      // One motor per track
      if (next_note.track == 0) {
        motor_set_note(&motor1, next_note);
      } else if (next_note.track == 1) {
        motor_set_note(&motor2, next_note);
      } else if (next_note.track == 2) {
        motor_set_note(&motor3, next_note);
      } else if (next_note.track == 3) {
        motor_set_note(&motor4, next_note);
      }

      note_index += 1;
      next_note = note_create(NOTE_TABLE[note_index]);
    }
  }
};
