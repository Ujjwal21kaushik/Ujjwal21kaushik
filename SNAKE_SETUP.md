# Fixing the contribution snake

The README uses plain image URLs (not Markdown links inside `src` or `srcset`). The SVG files are generated into the `output` branch by `.github/workflows/snake.yml`.

1. Put `README.md` in the root of `Ujjwal21kaushik/Ujjwal21kaushik`.
2. Also upload `.github/workflows/snake.yml` using that exact path.
3. Commit the changes to `main`.
4. Open the repository's **Actions** tab, select **Generate contribution snake**, and click **Run workflow**.
5. Wait for a successful run. It should create/update the `output` branch and the SVG files. Then refresh the profile page.

If the workflow fails, open its run and check the failed step. In repository settings, make sure Actions are enabled and workflow permissions allow writing repository contents.
