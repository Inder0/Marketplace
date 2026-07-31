# Marketplace

A full-stack online marketplace built with Django, where users can list products for sale, browse listings from other sellers, leave ratings/reviews, and complete purchases through an integrated payment gateway.

**Live demo:** [marketplace-bu5n.onrender.com](https://marketplace-bu5n.onrender.com/)

> Note: this is hosted on Render's free tier, so the first request after a period of inactivity may take 30–60 seconds to spin up. Please be patient!

---

## What it does

### For buyers
- **Browse & search products** – a paginated product feed with sorting (newest, price low→high, price high→low) and search
- **Product details** – images (multiple per product), price, and an average star rating with a review count (e.g. "★ 4.0 (1 review)"), with individual customer reviews shown further down the page
- **Seller profiles** – every product links back to a public seller profile
- **Checkout & payments** – add shipping details, confirm your order, then pay through Razorpay; once payment clears you land on a "Payment Successful" screen and the seller is notified to arrange delivery
- **Order history** – a personal orders page listing everything you've purchased, with the product image, price, seller, and purchase date
- **Authentication** – standard email/password login plus Google OAuth (via `django-allauth`)

### For sellers
- **My Products dashboard** – manage all your listings in one place, with per-product earnings, order count, and average rating, plus quick "Update" and "Details" actions and a button to add a new product
- **Analytics dashboard** – lifetime revenue, revenue in the last 30/7 days, total order count, a revenue-over-time chart, a recent orders feed, and a "Top Selling Products" leaderboard

### Platform
- **Image uploads** – product images are stored on Cloudinary rather than the local filesystem, so uploads persist across deploys
- **Payments** – checkout is wired up to Razorpay
- **REST API** – a documented API (via `drf-spectacular`) alongside the regular Django views, secured with JWT

---

## Checkout flow

Buying a product is a straightforward, four-step flow:

1. **Checkout** – enter (or confirm) your shipping name, phone number, and address
2. **Confirm Payment** – a summary screen showing the product, price, and shipping address one more time before you commit, with an option to edit the address
3. **Pay** – Razorpay's checkout modal opens (cards, netbanking, wallets, and more), currently running in test mode on the live demo
4. **Payment Successful** – you're dropped on a confirmation page, and the seller is expected to reach out on the phone number provided to arrange delivery

Once logged in, a top nav (Dashboard / Orders / Profile / Logout) makes it easy to jump between browsing, your purchase history, and your account.

---

## Tech stack

| Layer | Tools |
|---|---|
| Backend | Django 6, Django REST Framework |
| Auth | django-allauth (incl. Google OAuth), Simple JWT |
| Database | PostgreSQL (via `psycopg2` / `dj-database-url`) |
| Media storage | Cloudinary |
| Payments | Razorpay |
| Frontend | Django templates + HTMX + `django-widget-tweaks` |
| Static files | Whitenoise |
| Deployment | Gunicorn on Render |

---

## Project structure

```
Marketplace/
├── core/          # Django project settings, root URLconf
├── marketplace/   # Product listings, reviews, browsing logic
├── users/         # Auth, profiles, seller pages
├── api/           # DRF endpoints + schema
├── templates/      # Django templates
├── static/         # CSS/JS/images
├── manage.py
├── requirements.txt
└── Procfile         # Gunicorn start command for Render
```

---

## Running it locally

**1. Clone the repo**
```bash
git clone https://github.com/Inder0/Marketplace.git
cd Marketplace
```

**2. Create a virtual environment and install dependencies**
```bash
python -m venv venv
source venv/bin/activate   # venv\Scripts\activate on Windows
pip install -r requirements.txt
```

**3. Set up environment variables**

Create a `.env` file in the project root with something like:
```env
SECRET_KEY=your-django-secret-key
DEBUG=True
DATABASE_URL=postgres://user:password@localhost:5432/marketplace

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Google OAuth (optional, for social login)
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret

# Razorpay (optional, for payments)
RAZORPAY_KEY_ID=your-key-id
RAZORPAY_KEY_SECRET=your-key-secret
```

**4. Run migrations and start the server**
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` and you should be up and running.

---

## API docs

The API is documented via `drf-spectacular`. Once the server is running, the schema is typically browsable at `/api/schema/swagger-ui/` (check `core/urls.py` if the route has changed).

---

## Deployment

The app is configured to run on Render using the included `Procfile`:
```
web: gunicorn core.wsgi
```
Static files are served with Whitenoise, and product images are offloaded to Cloudinary so they aren't lost on redeploy.

---

## Roadmap / ideas

- Wishlist / saved items
- In-app messaging between buyers and sellers
- Verified-purchase badge on reviews
- Seller replies to reviews

---

## Author

Built by [Inder0](https://github.com/Inder0).

Contributions, issues, and suggestions are welcome — feel free to open a PR or issue.
