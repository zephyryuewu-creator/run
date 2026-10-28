# NRC outdoor data integration

Use the existing Nike API endpoints and the original Dashboard Activity contract. Preserve the current mile-based Excel importer for indoor runs. Fetch NRC outdoor runs directly with NIKE_ACCESS_TOKEN from GitHub Actions Secrets. Keep real GPS routes and active duration, use America/New_York dates, and never invent indoor GPS or heart rate. Persist NRC input separately so subsequent Excel uploads retain outdoor history.

Approaches: direct Nike API follows the user-selected upstream integration and can import existing Nike history. Strava is an alternative but the official Nike connection does not backfill earlier activities. Manual Excel entry loses outdoor GPS and is reserved for treadmill runs.

The token is temporary and the existing upstream script does not refresh it automatically. Provide a manual Sync Nike Run Club workflow; updating Excel continues to publish automatically using the last successfully imported NRC data. Leave Dashboard components and styles untouched.

Verification: failing regression test before implementation; nine Python tests; live Nike response; combined real data; Node unit tests; production build; deployed public page.
