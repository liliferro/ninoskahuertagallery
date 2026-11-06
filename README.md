# Ninoska Huerta Gallery — website prototype

Prototype of the new Ninoska Huerta Gallery website, built on the rebrand (brand book v2) and on all the content of the current site, ninoskahuertagallery.com. It is planned to move to Shopify.

## Open it

Open `index.html` or serve the repository root. Fonts, CSS and part of the images are files under `assets/` and `media/`. Regenerate the HTML with `python3 src/build_site.py`. The heavy source images that are not in `media/` still load from ninoskahuertagallery.com; the list is `media/manifest.json`.

## What it includes

- **Home:** the kinetic hero (Physichromie lamellae + Soto-style moiré, follows the pointer, "Pausar movimiento" button, respects reduced motion, 30 fps on small screens).
- **Home sections:** the gallery intro, the featured exhibition (Marcos Marín, *Beyond the Visible*), the artists with the featured artist (Amalia Pereira), the latest exhibitions, a store selection, the latest blog posts, videos, the newsletter and the footer.
- **Pages:** About, Artists (26), Exhibitions (29), Shop (16 products with filters and sorting), product page with specifications, Blog (8 posts) and Contact (form, address, phone, email, social links).
- **Cart:** add to cart, quantities, removal and subtotal. It is saved in the visitor's browser.

## Not yet connected (needed for Shopify)

- The cart and checkout are a front-end prototype. In Shopify they become the theme's cart and checkout (Storefront/Cart API).
- The contact form opens the visitor's email app. The newsletter form only confirms that the address was not stored. Shopify's native contact and customer forms replace them.
- Some images are served from `media/` as WebP and AVIF. The rest still load from the current site's `wp-content/uploads` (see `media/manifest.json`).
- Artist, exhibition, product and blog URLs are real pages on this site (`/artistas/`, `/exposiciones/`, `/tienda/`, `/blog/`).

## Source

`src/` holds the editable source: `page.html` (previous single-page structure), `content/content.js` and `data.js` (migrated content), `build_site.py` (writes one HTML file per URL, the sitemap, robots.txt and llms.txt) and `fetch_media.py` (WebP/AVIF for the heaviest and above-the-fold images). Styles and behavior are `assets/site.css`, `assets/app.js` and `assets/kinetic.js`.
