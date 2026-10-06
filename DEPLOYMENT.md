# GitHub Pages deployment

Repository: `jmgasper/airos-website` (public). Publishing source: **GitHub Actions**.
The workflow `.github/workflows/pages.yml` builds and validates the site before
deploying to the `github-pages` environment. All source API access is read-only.
Only the deployment job needs permission to publish Pages.

Until DNS is connected, the preview can run at
`https://jmgasper.github.io/airos-website/`. Its asset paths are generated from
`actions/configure-pages` outputs. Setting the custom domain switches the next
build to root-relative paths without editing the website.

## Connect airos.works

At the time of initial setup the domain used Namecheap's registrar-servers.com
nameservers and an apex parking/redirect address. Keep unrelated MX/TXT records.

1. Optionally verify `airos.works` in the GitHub account's Pages settings,
   using the TXT record GitHub supplies.
2. Add `airos.works` as this repository's Pages custom domain before routing
   DNS to GitHub.
3. Replace the apex parking/URL-redirect record with these four A records:

   | Type | Host | Value |
   |---|---|---|
   | A | @ | 185.199.108.153 |
   | A | @ | 185.199.109.153 |
   | A | @ | 185.199.110.153 |
   | A | @ | 185.199.111.153 |
   | CNAME | www | jmgasper.github.io |

   Optionally add the four GitHub IPv6 AAAA records:
   `2606:50c0:8000::153`, `2606:50c0:8001::153`,
   `2606:50c0:8002::153`, `2606:50c0:8003::153`.
4. Run the Pages workflow once after changing the custom domain, then verify
   both the apex and `www` through DNS and HTTP.
5. Once GitHub issues its certificate, enable **Enforce HTTPS** and verify
   `https://airos.works/` and its subpages.

Authoritative instructions:
[Managing a GitHub Pages custom domain](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)
and [HTTPS](https://docs.github.com/en/pages/getting-started-with-github-pages/securing-your-github-pages-site-with-https).

DNS access is separate from repository access. A deployed preview is not proof
that the custom domain is connected; DNS, a valid certificate and the actual
response from airos.works must all be checked.
