-- Seed data for the exercises table. Not part of schema.sql (that's structure only) —
-- run this once by hand after the table exists:
--   psql -d training_plan -f scripts/seed_exercises.sql

INSERT INTO exercises (name, muscle_group, complements_lift, equipment_access, stresses) VALUES
-- Bench accessories (chest / triceps / front delts)
('Incline Dumbbell Press',        'chest',      ARRAY['bench'],                        'home basic',      ARRAY['shoulders']),
('Close-Grip Bench Press',        'triceps',    ARRAY['bench'],                        'full gym',        ARRAY['wrists', 'elbows']),
('Cable Fly',                     'chest',      ARRAY['bench'],                        'full gym',        ARRAY['shoulders']),
('Push-ups',                      'chest',      ARRAY['bench'],                        'bodyweight only', ARRAY['wrists']),
('Tricep Pushdown',               'triceps',    ARRAY['bench'],                        'full gym',        ARRAY['elbows']),
('Overhead Tricep Extension',     'triceps',    ARRAY['bench'],                        'home basic',      ARRAY['elbows']),
('Dumbbell Floor Press',          'chest',      ARRAY['bench'],                        'home basic',      ARRAY[]::text[]),
('Diamond Push-ups',              'triceps',    ARRAY['bench'],                        'bodyweight only', ARRAY['wrists', 'elbows']),
('Decline Bench Press',           'chest',      ARRAY['bench'],                        'full gym',        ARRAY['shoulders']),
('Resistance Band Chest Press',   'chest',      ARRAY['bench'],                        'bodyweight only', ARRAY[]::text[]),
('Skull Crushers',                'triceps',    ARRAY['bench'],                        'full gym',        ARRAY['elbows']),

-- Squat accessories (quads / glutes / core)
('Leg Press',                     'quads',      ARRAY['squat'],                        'full gym',        ARRAY['knees', 'lower back']),
('Walking Lunges',                'quads',      ARRAY['squat'],                        'home basic',      ARRAY['knees']),
('Bodyweight Squats',             'quads',      ARRAY['squat'],                        'bodyweight only', ARRAY['knees']),
('Leg Extension',                 'quads',      ARRAY['squat'],                        'full gym',        ARRAY['knees']),
('Bulgarian Split Squat',         'quads',      ARRAY['squat'],                        'home basic',      ARRAY['knees', 'ankles']),
('Goblet Squat',                  'quads',      ARRAY['squat'],                        'home basic',      ARRAY['knees']),
('Plank',                         'core',       ARRAY['squat', 'deadlift'],            'bodyweight only', ARRAY[]::text[]),
('Glute Bridge',                  'glutes',     ARRAY['squat', 'deadlift'],            'bodyweight only', ARRAY['lower back']),
('Step-ups',                      'quads',      ARRAY['squat'],                        'home basic',      ARRAY['knees']),
('Wall Sit',                      'quads',      ARRAY['squat'],                        'bodyweight only', ARRAY['knees']),
('Hack Squat Machine',            'quads',      ARRAY['squat'],                        'full gym',        ARRAY['knees', 'lower back']),

-- Deadlift accessories (hamstrings / glutes / lower back)
('Romanian Deadlift (dumbbell)',  'hamstrings', ARRAY['deadlift'],                     'home basic',      ARRAY['lower back']),
('Barbell Hip Thrust',            'glutes',     ARRAY['deadlift'],                     'full gym',        ARRAY['lower back', 'hips']),
('Back Extension',                'lower back', ARRAY['deadlift'],                     'full gym',        ARRAY['lower back']),
('Cable Pull-through',            'hamstrings', ARRAY['deadlift'],                     'full gym',        ARRAY['lower back']),
('Good Mornings',                 'hamstrings', ARRAY['deadlift'],                     'full gym',        ARRAY['lower back']),
('Dead Bug',                      'core',       ARRAY['squat', 'deadlift'],            'bodyweight only', ARRAY[]::text[]),
('Seated Leg Curl',               'hamstrings', ARRAY['deadlift'],                     'full gym',        ARRAY['knees']),
('Kettlebell Swing',              'hamstrings', ARRAY['deadlift'],                     'home basic',      ARRAY['lower back']),
('Superman',                      'lower back', ARRAY['deadlift'],                     'bodyweight only', ARRAY[]::text[]),
('Trap Bar Deadlift',             'hamstrings', ARRAY['deadlift'],                     'full gym',        ARRAY['lower back', 'knees']),

-- Overhead press accessories (shoulders / triceps / upper back)
('Lateral Raise',                 'shoulders',  ARRAY['overhead press'],               'home basic',      ARRAY['shoulders']),
('Face Pull',                     'upper back', ARRAY['overhead press', 'barbell row'],'full gym',        ARRAY['shoulders', 'neck']),
('Arnold Press',                  'shoulders',  ARRAY['overhead press'],               'home basic',      ARRAY['shoulders']),
('Pike Push-ups',                 'shoulders',  ARRAY['overhead press'],               'bodyweight only', ARRAY['wrists', 'shoulders']),
('Front Raise',                   'shoulders',  ARRAY['overhead press'],               'home basic',      ARRAY['shoulders']),
('Landmine Press',                'shoulders',  ARRAY['overhead press'],               'full gym',        ARRAY['shoulders']),
('Seated Dumbbell Shoulder Press','shoulders',  ARRAY['overhead press'],               'home basic',      ARRAY['shoulders']),
('Wall Handstand Hold',           'shoulders',  ARRAY['overhead press'],               'bodyweight only', ARRAY['wrists', 'shoulders']),

-- Barbell row accessories (back / biceps)
('Lat Pulldown',                  'back',       ARRAY['barbell row'],                  'full gym',        ARRAY['shoulders']),
('Dumbbell Row',                  'back',       ARRAY['barbell row'],                  'home basic',      ARRAY['lower back']),
('Bicep Curl (dumbbell)',         'biceps',     ARRAY['barbell row'],                  'home basic',      ARRAY['elbows']),
('Pull-ups',                      'back',       ARRAY['barbell row'],                  'bodyweight only', ARRAY['shoulders', 'elbows']),
('Inverted Row',                  'back',       ARRAY['barbell row'],                  'bodyweight only', ARRAY[]::text[]),
('Seated Cable Row',              'back',       ARRAY['barbell row'],                  'full gym',        ARRAY['lower back']),
('Hammer Curl',                   'biceps',     ARRAY['barbell row'],                  'home basic',      ARRAY['elbows', 'wrists']),
('T-Bar Row',                     'back',       ARRAY['barbell row'],                  'full gym',        ARRAY['lower back', 'upper back']),
('Resistance Band Row',           'back',       ARRAY['barbell row'],                  'bodyweight only', ARRAY[]::text[]),
('Reverse Fly (dumbbell)',        'upper back', ARRAY['barbell row'],                  'home basic',      ARRAY['shoulders']);
