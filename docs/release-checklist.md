# Release acceptance

- Confirm latest PR Browser QA succeeds and inspect screenshots at 320, 390, 768, 1440 px.
- Inspect Lighthouse JSON: performance >=90, accessibility, best practices and SEO >=95. Workflow success alone does not enforce these thresholds.
- Confirm official event dates, social links, recording link, image permissions and Android browser operation.
- Obtain explicit merge and publication approval. Merge PR, then wait for Browser QA on the exact main SHA.
- Configure repository Pages source as GitHub Actions. Dispatch Publish verified release on main with the successful main QA run ID and PUBLISH confirmation.
- Verify public URL https://celticmusic-nagoya.github.io/banna-beag/ including assets, navigation, metadata and mobile rendering. Record deployed SHA and run ID.
- Rollback: revert the offending main change through a reviewed PR, run QA on the new main SHA and publish its verified artifact. Do not bypass integrity checks.

Known limitations: independent final visual acceptance, Android device test, Pages configuration and live deployment remain unverified. The recording card reuses an approved activity photo; replacement with a distinct verified official photo is optional before release.
