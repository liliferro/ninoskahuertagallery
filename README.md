# Ninoska Huerta Gallery — website prototype

Prototype of the new Ninoska Huerta Gallery website, built on the rebrand (brand book v2) and on all the content of the current site, ninoskahuertagallery.com. It is planned to move to Shopify.

## Open it

`index.html` is a single self-contained file (fonts and logos embedded). Open it in a browser or publish it on any static host (GitHub Pages, Netlify, Vercel).

## What it includes

- **Home:** the kinetic hero (Physichromie lamellae + Soto-style moiré, follows the pointer, "Pausar movimiento" button, respects reduced motion, 30 fps on small screens).
- **Home sections:** the gallery intro, the featured exhibition (Marcos Marín, *Beyond the Visible*), the artists with the featured artist (Amalia Pereira), the latest exhibitions, a store selection, the latest blog posts, videos, the newsletter and the footer.
- **Pages:** About, Artists (26), Exhibitions (29), Shop (16 products with filters and sorting), product page with specifications, Blog (8 posts) and Contact (form, address, phone, email, social links).
- **Cart:** add to cart, quantities, removal and subtotal. It is saved in the visitor's browser.

## Not yet connected (needed for Shopify)

- The cart and checkout are a front-end prototype. In Shopify they become the theme's cart and checkout (Storefront/Cart API).
- The contact form opens the visitor's email app. The newsletter form only shows a confirmation. Shopify's native contact and customer forms replace them.
- Product, artist, exhibition and blog images still load from the current site's `wp-content/uploads`. Move them to Shopify Files before the old site is switched off.
- The detail pages for artists, exhibitions and blog posts still link to the current site. Migrate them as Shopify pages, collections and blog articles.

## Source

`src/` holds the editable source: `page.html` (structure and styles), `app.js` (logic and kinetic hero), `data.js` (all migrated content: products, artists, exhibitions and posts) and `build.py` (assembles `index.html`, embedding the fonts and logos).
