-- ============================================================================
-- Two-Variable Tolerance Slope Update
-- ============================================================================
-- For two-variable statistics (where result_x_unit IS NOT NULL), tolerance
-- bounds should be a linear function of result_x rather than fixed values.
--
-- This script updates Hinge and Doorcheck Performance (Sampled) as the first
-- implementation: lower_lim = 53 * result_x, upper_lim = 67 * result_x.
-- ============================================================================

BEGIN;

UPDATE auto_door_stats
SET
    result_y_lower_lim = ROUND((53.0 * result_x)::numeric, 1),
    result_y_upper_lim = ROUND((67.0 * result_x)::numeric, 1)
WHERE
    auto_door_stat_name = 'Hinge and Doorcheck Performance (Sampled)';

-- Verification
SELECT
    'Hinge and Doorcheck Performance (Sampled)' AS stat_name,
    COUNT(*)                                    AS updated_rows,
    MIN(result_y_lower_lim)                     AS min_lower,
    MAX(result_y_lower_lim)                     AS max_lower,
    MIN(result_y_upper_lim)                     AS min_upper,
    MAX(result_y_upper_lim)                     AS max_upper
FROM auto_door_stats
WHERE auto_door_stat_name = 'Hinge and Doorcheck Performance (Sampled)';

COMMIT;
