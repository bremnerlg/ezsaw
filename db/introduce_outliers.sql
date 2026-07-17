-- Ensure every VIN has outliers at every door so the app never shows
-- an empty graph regardless of which door is selected.
--
-- Strategy: for each vehicle, for each door, pick one of the 9 stats
-- and push result_y well outside [result_y_lower, result_y_upper].

BEGIN;

DO $$
DECLARE
  rec RECORD;
  r double precision;
  flip_row int;
  row_idx int;
  cnt int := 0;
  new_y numeric;
  lo numeric;
  up numeric;
BEGIN
  FOR rec IN
    SELECT s.vin, s.door, s.fk_steps_auto_door_stats,
           a.result_y_lower_lim, a.result_y, a.result_y_upper_lim,
           ROW_NUMBER() OVER (PARTITION BY s.vin, s.door ORDER BY s.fk_steps_auto_door_stats) AS rn
    FROM steps s
    JOIN auto_door_stats a ON s.fk_steps_auto_door_stats = a.auto_door_stat_id
    ORDER BY s.vin, s.door, s.fk_steps_auto_door_stats
  LOOP
    -- Make stat #3 (rn=3) an outlier for every VIN/door block
    IF rec.rn = 3 THEN
      lo := rec.result_y_lower_lim;
      up := rec.result_y_upper_lim;
      r := random();
      IF r < 0.5 THEN
        -- below lower limit
        new_y := lo - (random() * GREATEST(lo, 0.5) + 0.1);
      ELSE
        -- above upper limit
        new_y := up + (random() * GREATEST(up, 0.5) + 0.1);
      END IF;
      UPDATE auto_door_stats
      SET result_y = new_y
      WHERE auto_door_stat_id = rec.fk_steps_auto_door_stats;
      cnt := cnt + 1;
    END IF;
  END LOOP;
  RAISE NOTICE 'Rows made into outliers (1 per VIN/door block): %', cnt;
END $$;

-- Also add a few extras for demo variety (additional random outliers)
UPDATE auto_door_stats
SET result_y = result_y_upper_lim + (random() * GREATEST(result_y_upper_lim, 0.5) + 0.1)
WHERE random() < 0.02
  AND result_y BETWEEN result_y_lower_lim AND result_y_upper_lim;

UPDATE auto_door_stats
SET result_y = result_y_lower_lim - (random() * GREATEST(result_y_lower_lim, 0.5) + 0.1)
WHERE random() < 0.02
  AND result_y BETWEEN result_y_lower_lim AND result_y_upper_lim;

-- Verify
SELECT 'outliers_found' as info, COUNT(*) FROM auto_door_stats
WHERE result_y < result_y_lower_lim OR result_y > result_y_upper_lim;

SELECT 'total_stats' as info, COUNT(*) FROM auto_door_stats;

COMMIT;
