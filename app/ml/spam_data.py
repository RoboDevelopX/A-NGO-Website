"""Synthetic training data for the contact-form spam classifier.

READ THIS BEFORE TRUSTING THE MODEL: every example here is generated from templates I
wrote. Real spam is more varied, changes over time and is adversarial. The model learns
these templates, so its test scores describe how well it separates *my* templates, not how
it will do on real traffic. It is a starting point to be retrained on real, labelled
submissions (the admin's spam filter view is where those labels would come from).

To make the evaluation less flattering, every example carries the id of the template it
came from, and the training script splits train/test *by template*: the test set only
contains phrasings the model never saw during training.

We include deliberately hard cases on both sides: genuine messages with links, prices and
words like "free"; spam with no links at all; and Hinglish on both sides.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

HAM, SPAM = 0, 1


@dataclass(frozen=True)
class Sample:
    text: str
    label: int
    template_id: str


FIRST_NAMES = [
    "Priya", "Rahul", "Ananya", "Vikram", "Meera", "Arjun", "Kavya", "Rohan", "Sneha", "Imran",
    "Fatima", "Sandeep", "Lakshmi", "Aditya", "Pooja", "Harpreet", "Nisha", "Karthik", "Zoya",
    "Deepak", "Asha", "Manoj", "Divya", "Suresh", "Neha", "Abdul", "Gurpreet", "Ritika",
]  # fmt: skip
LAST_NAMES = [
    "Sharma", "Iyer", "Khan", "Patel", "Reddy", "Singh", "Nair", "Gupta", "Das", "Joshi",
    "Mehta", "Soren", "Oraon", "Choudhary", "Banerjee", "Kaur", "Menon", "Qureshi", "Rao",
]  # fmt: skip
CITIES = ["Jaipur", "Ranchi", "Bengaluru", "Pune", "Delhi", "Kolkata", "Udaipur", "Mumbai",
          "Hyderabad", "Bikaner", "Chennai", "Jodhpur", "Lucknow"]  # fmt: skip
JOBS = ["software engineer", "school teacher", "college student", "data analyst",
        "retired bank manager", "nurse", "graphic designer", "chartered accountant",
        "product manager", "homemaker", "PhD student", "content writer", "photographer"]  # fmt: skip
ACTIVITIES = ["teaching reading", "maths tutoring", "mentoring girls", "running a Code Club",
              "sorting library books", "event support", "photography", "social media",
              "fundraising", "data entry", "worksheet design"]  # fmt: skip
DAYS = ["weekends", "Saturday mornings", "weekday evenings", "Sundays", "two days a month",
        "after 6 pm on weekdays", "during my summer break"]  # fmt: skip
COMPANIES = ["company", "firm", "bank", "school trust", "family foundation", "startup"]
ACRONYMS = ["CSR", "NSS", "NCC", "IIT", "HR", "IT"]
MONTHS = ["January", "March", "June", "August", "October", "December"]
ORGS = ["our company", "our school", "my college NSS unit", "our Rotary club",
        "our CSR team", "my office volunteering group"]  # fmt: skip

SPAM_PRODUCTS = ["SEO services", "website traffic", "Instagram followers", "backlinks",
                 "crypto signals", "weight loss pills", "replica watches", "cheap loans",
                 "forex trading course", "YouTube views", "email lists"]  # fmt: skip
SPAM_DOMAINS = ["best-seo-ranker.xyz", "cheap-followers.top", "crypto-profit.click",
                "quickloan-now.biz", "rank1-google.info", "wealth-hack.site"]  # fmt: skip
SPAM_NAMES = ["SEO Expert", "Crypto King", "Digital Marketing Team", "Loan Agent",
              "Web Solutions", "Rich Dad"]  # fmt: skip

HAM_TEMPLATES: dict[str, str] = {
    "ham_intro": "Hi, I'm a {job} from {city} and I'd love to help with {activity} on {days}.",
    "ham_teacher": "I have taught Class {n} for {years} years in {city}. Happy to support your reading groups on {days}.",
    "ham_student": "I am a {job} in {city} looking for volunteering on {days}. I can help with {activity}.",
    "ham_link": "Hello, I'm {first}, a {job}. My portfolio is at https://{first_lower}{n}.github.io if you need help with {activity}.",
    "ham_linkedin": "Hi team, sharing my LinkedIn https://www.linkedin.com/in/{first_lower}-{last_lower} so you can see my background. I'd like to help with {activity}.",
    "ham_free": "I'm free on {days} and would like to offer free {activity} sessions for the children.",
    "ham_donation_q": "I donated Rs {amount} last month but haven't received my 80G receipt yet. Could you check please?",
    "ham_csr": "I lead CSR at a mid-size firm in {city}. We'd like to discuss funding {n} learning centres next year. What's the best way to connect?",
    "ham_media": "I'm a journalist with a {city} daily writing about girls' education. Could I interview someone from your Jharkhand team?",
    "ham_group": "Writing on behalf of {org}. About {n} of us want to volunteer together for your book drive on {days}.",
    "ham_question": "Do you need volunteers to know Hindi? I speak English and some Marwari. I can do {activity}.",
    "ham_hinglish": "Namaste, main {city} se hoon aur {days} ko bachon ko padhana chahti hoon. Kaise judun?",
    "ham_hinglish2": "Mujhe {activity} mein madad karni hai. Main {job} hoon, {days} free hoon.",
    "ham_photo": "I'm an amateur photographer. Could I volunteer to take pictures at the {city} event? Happy to share all photos for free.",
    "ham_short": "Interested in {activity}. Available {days}. Please let me know next steps.",
    "ham_parent": "My daughter studies in Class {n} near {city}. Is there a learning centre in our village she could join?",
    "ham_alumni": "I was a student at your Barmer centre in 2016 and now I'm a {job}. I want to give back by {activity}.",
    "ham_corporate_email": "Please contact me at {first_lower}.{last_lower}@company.example about a payroll giving partnership.",
    "ham_books": "We have around {n}0 children's books in good condition. Can we donate them to your library corners?",
    "ham_feedback": "Loved the post about teaching at the right level! We use something similar at {org}. Would love to compare notes.",
    "ham_tech": "I'm a {job} and can help set up offline Scratch on your tablets. I have done this for {n} schools before.",
    "ham_price": "Our printing press can print {n}00 workbooks at cost price (around Rs {amount}). Would that help your centres?",
    # Short, formal messages with acronyms, years and phone numbers. Without these the model
    # learned that "short + capitals + digits" means spam (see TextStatsTransformer).
    "ham_short_csr": "Our {company} would like to discuss {acronym} support for {year}.",
    "ham_call_me": "Please call me on +91 {phone} after 6 pm. I can help with {activity}.",
    "ham_visit": "Can our {acronym} group visit the {city} centre in {month} {year}?",
}

SPAM_TEMPLATES: dict[str, str] = {
    "spam_seo": "Want your website on the first page of Google? We offer {product} at the lowest price. Visit http://{domain} now!",
    "spam_seo2": "Dear Sir/Madam, I noticed your website is not ranking. Our {product} package guarantees #1 ranking in 7 days. Reply YES.",
    "spam_crypto": "Earn {pct}% daily profit with our {product}!!! Join now: https://{domain}/join Limited slots!!!",
    "spam_crypto_nolink": "Invest Rs {amount} today and get {pct}x returns in one week. 100% guaranteed. WhatsApp me on +1 {phone}.",
    "spam_loan": "Instant loan approved without documents. Get up to Rs {amount}000 in 10 minutes. Apply: http://{domain}",
    "spam_prize": "CONGRATULATIONS!!! Your email has won ${amount},000 in our annual lottery. Send your bank details to claim.",
    "spam_followers": "Buy {product} cheap!! 10,000 for just ${pct}. Fast delivery. {domain}",
    "spam_backlinks": "Hello webmaster, we sell high DA {product} for your site. Check our price list at https://{domain}/prices",
    "spam_pharma": "Best {product} without prescription, discreet shipping worldwide. Order at {domain} - 70% OFF today only",
    "spam_job": "Work from home and earn Rs {amount},000 per week. No experience needed. Contact on Telegram @{handle}",
    "spam_hinglish": "Ghar baithe kamaye Rs {amount},000 mahina! Abhi register karein: http://{domain}",
    "spam_hinglish2": "Sirf Rs {pct}99 mein {product} paayein. Offer aaj raat tak. Call karo {phone}",
    "spam_web": "We noticed your website could use a redesign. We build websites for just ${pct}9. Email us at sales@{domain}",
    "spam_gibberish": "{product} {product} best price click here {domain} {domain} cheap cheap",
    "spam_inheritance": "I am a lawyer representing a late client with no heirs. I need your help to transfer USD {amount} million. Kindly reply urgently.",
    "spam_casino": "Play online casino and win big! Get {pct}0 free spins on signup at https://{domain}",
    "spam_reseller": "Become a reseller of our {product} and earn huge commission. WhatsApp {phone} for details.",
    "spam_review": "We can post 50 five-star reviews for your organisation for only ${pct}. Boost your reputation fast!",
    "spam_unsubscribe": "Exclusive offer on {product}. To stop receiving these emails click http://{domain}/unsubscribe",
    "spam_short_link": "check this out http://{domain}/x{n}",
    "spam_urgent": "URGENT: Your account will be suspended. Verify your details immediately at http://{domain}/verify",
}


def _fill(template: str, rng: random.Random) -> str:
    first = rng.choice(FIRST_NAMES)
    last = rng.choice(LAST_NAMES)
    values = {
        "first": first,
        "first_lower": first.lower(),
        "last_lower": last.lower(),
        "job": rng.choice(JOBS),
        "city": rng.choice(CITIES),
        "activity": rng.choice(ACTIVITIES),
        "days": rng.choice(DAYS),
        "org": rng.choice(ORGS),
        "n": rng.randint(2, 9),
        "years": rng.randint(2, 25),
        "amount": rng.choice([500, 1000, 2500, 5000, 10000, 25000]),
        "product": rng.choice(SPAM_PRODUCTS),
        "domain": rng.choice(SPAM_DOMAINS),
        "pct": rng.randint(2, 9),
        "phone": f"{rng.randint(200, 999)} {rng.randint(100, 999)} {rng.randint(1000, 9999)}",
        "handle": rng.choice(["earnfast", "richquick", "moneybot", "cryptoguru"]),
        "company": rng.choice(COMPANIES),
        "acronym": rng.choice(ACRONYMS),
        "year": rng.randint(2026, 2028),
        "month": rng.choice(MONTHS),
    }
    return template.format(**values)


def _name(label: int, rng: random.Random) -> str:
    if label == SPAM and rng.random() < 0.4:
        return rng.choice(SPAM_NAMES)
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"


# Hand-written messages that never go into training: a quick sanity check printed by
# scripts/train_spam.py and asserted in the tests. They were written while fixing the
# false positive described in TextStatsTransformer, so they are a *development* check,
# not an unbiased test set.
HANDWRITTEN_HAM: list[tuple[str, str]] = [
    ("Rohan Gupta", "Our company would like to discuss CSR in 2027."),
    ("Anita Desai", "Can I visit one of your learning centres next month with my students?"),
    ("Kiran Shah", "How do I get a tax receipt for my donation?"),
    (
        "Sunil Verma",
        "We are a small business in Jaipur and want to sponsor school bags for 50 children.",
    ),
    ("Meera Iyer", "Is there a volunteering opportunity for college students in Ranchi?"),
    ("Fatima Khan", "I'd like to set up a monthly donation. What's the best way?"),
    ("Arjun Nair", "Our team of 12 engineers wants to spend a day at a centre. Is that possible?"),
    ("Pooja Rao", "Please call me on 98290 12345. I can teach English on Sundays."),
]
HANDWRITTEN_SPAM: list[tuple[str, str]] = [
    (
        "Web Solutions",
        "We build websites for NGOs at the lowest price. Visit http://quickloan-now.biz",
    ),
    ("Mark", "URGENT business proposal. Kindly send your bank details to receive USD 4.5 million."),
    ("Crypto Desk", "Double your money in 7 days!!! Guaranteed profit, WhatsApp +44 7700 900123"),
    ("SEO Team", "Get 10,000 Instagram followers for $9. Fast delivery. cheap-followers.top"),
]


def classifier_text(name: str, message: str) -> str:
    """The exact text the classifier sees, used for both training and live scoring."""
    return f"{name}\n{message}"


def generate_dataset(n_per_class: int = 600, seed: int = 42) -> list[Sample]:
    """Balanced, shuffled, fully deterministic for a given seed."""
    rng = random.Random(seed)
    samples: list[Sample] = []
    for label, templates in ((HAM, HAM_TEMPLATES), (SPAM, SPAM_TEMPLATES)):
        ids = list(templates)
        for i in range(n_per_class):
            template_id = ids[i % len(ids)]
            message = _fill(templates[template_id], rng)
            samples.append(Sample(classifier_text(_name(label, rng), message), label, template_id))
    rng.shuffle(samples)
    return samples
