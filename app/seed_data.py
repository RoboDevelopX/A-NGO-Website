"""Demo content for events and blog posts. Everything here is fictional.

Event dates are *relative* to the day you run the seed, so the demo always has upcoming and
past events no matter when someone clones the repo.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EventSeed:
    slug: str
    title: str
    summary: str
    body: str
    location: str
    days_from_now: int
    weekday: int | None  # 0=Monday ... 6=Sunday; moves the date forward to that weekday
    start: tuple[int, int]  # local IST (hour, minute)
    duration_hours: float
    tags: tuple[str, ...]
    image: str
    image_alt: str
    is_online: bool = False
    capacity: int | None = None


@dataclass(frozen=True)
class PostSeed:
    slug: str
    title: str
    excerpt: str
    body: str
    author: str
    author_role: str
    tags: tuple[str, ...]
    days_ago: int
    image: str
    image_alt: str


EVENTS: list[EventSeed] = [
    EventSeed(
        slug="saturday-reading-mela-barmer",
        title="Saturday Reading Mela, Barmer",
        summary="A morning of read-alouds, story games and a book swap for 300 children and their families.",
        body=(
            "Our Barmer centres come together for a reading festival in the government school grounds.\n\n"
            "## What happens on the day\n\n"
            "- Read-aloud corners in Marwari, Hindi and English\n"
            "- A 'first full book' ceremony for children who finished their first storybook this term\n"
            "- A book swap table where every child takes a new book home\n\n"
            "## How volunteers help\n\n"
            "We need 20 volunteers to run reading corners and the book swap. No experience needed: "
            "you'll get a 30-minute briefing at 8:30 AM."
        ),
        location="Government Senior Secondary School grounds, Barmer, Rajasthan",
        days_from_now=5,
        weekday=5,
        start=(9, 0),
        duration_hours=4,
        tags=("library", "events", "teaching", "rajasthan"),
        capacity=60,
        image="/static/img/scenes/reading-circle.svg",
        image_alt="Five children sit in a circle on a mat under a large tree, each holding an open book.",
    ),
    EventSeed(
        slug="volunteer-orientation-online",
        title="New volunteer orientation (online)",
        summary="A 90-minute introduction to how our centres work and where volunteers make the biggest difference.",
        body=(
            "Thinking of volunteering with us? Start here. This session covers:\n\n"
            "1. How a learning centre runs, from attendance to reading groups\n"
            "2. Child safeguarding: our code of conduct and what it means in practice\n"
            "3. Remote roles: worksheet design, data entry, social media and mentoring calls\n\n"
            "The session is on Google Meet. You'll get the link by email the day before."
        ),
        location="Online",
        days_from_now=8,
        weekday=2,
        start=(18, 30),
        duration_hours=1.5,
        tags=("online", "teaching", "mentoring", "content", "digital"),
        capacity=100,
        is_online=True,
        image="/static/img/scenes/digital-corner.svg",
        image_alt="Two children share a tablet at a low table while a third points at the screen.",
    ),
    EventSeed(
        slug="teacher-fellowship-open-house-ranchi",
        title="Teacher Fellowship open house, Ranchi",
        summary="Meet our fellows and coaches, sit in on a demo class and learn how to apply for the 2027 cohort.",
        body=(
            "The Akshar Teacher Fellowship trains young women from rural Jharkhand to run learning "
            "centres in their own villages.\n\n"
            "At the open house you can watch a live demo of a 'teaching at the right level' class, "
            "meet current fellows, and ask our coaches anything. Applications for the 2027 cohort "
            "open the same week.\n\n"
            "Volunteers with a teaching background are welcome to join as observers and give feedback."
        ),
        location="Akshar regional office, Morabadi, Ranchi, Jharkhand",
        days_from_now=14,
        weekday=3,
        start=(11, 0),
        duration_hours=3,
        tags=("teaching", "mentoring", "jharkhand"),
        capacity=40,
        image="/static/img/scenes/teacher-training.svg",
        image_alt="A teacher stands at a blackboard explaining letters to a group of trainee teachers.",
    ),
    EventSeed(
        slug="girls-football-life-skills-camp-gumla",
        title="Girls' football and life-skills camp, Gumla",
        summary="A two-day camp for 120 girls in Classes 7 to 9: football in the mornings, life skills in the afternoons.",
        body=(
            "Sport keeps girls coming back. This camp mixes football coaching with sessions on "
            "goal-setting, money basics and staying in school.\n\n"
            "We are looking for women volunteers to lead small mentoring circles of 8 to 10 girls, "
            "and for anyone who can help with registration, lunch and first aid."
        ),
        location="Block stadium, Gumla, Jharkhand",
        days_from_now=20,
        weekday=5,
        start=(8, 0),
        duration_hours=8,
        tags=("mentoring", "events", "jharkhand"),
        capacity=30,
        image="/static/img/scenes/girls-football.svg",
        image_alt="Girls in school uniforms play football on a dusty field at sunset.",
    ),
    EventSeed(
        slug="code-club-launch-jaipur",
        title="Code Club launch weekend, Jaipur",
        summary="Launching offline coding clubs with Scratch on our solar tablet kits. Tech volunteers wanted.",
        body=(
            "Our digital corners now run Scratch offline. This weekend we train 25 teachers and "
            "launch the first Code Clubs with children from our Jaipur rural centres.\n\n"
            "If you work in tech, this is the event for you: pair with a teacher, help children "
            "build their first animation, and share what you do for a living."
        ),
        location="Akshar Learning Hub, Chomu, Jaipur district, Rajasthan",
        days_from_now=27,
        weekday=6,
        start=(10, 0),
        duration_hours=6,
        tags=("digital", "teaching", "events", "rajasthan"),
        capacity=25,
        image="/static/img/scenes/digital-corner.svg",
        image_alt="Two children share a tablet at a low table while a third points at the screen.",
    ),
    EventSeed(
        slug="walk-for-akshar-jaipur",
        title="Walk for Akshar 2026, Jaipur",
        summary="Our annual 5 km fundraising walk around Jal Mahal. Every walker funds a month of classes for one child.",
        body=(
            "Join 1,500 walkers for our biggest fundraiser of the year. Registration is free; we "
            "ask each walker to raise at least ₹1,000 from friends and family.\n\n"
            "Volunteers help with route marshalling, the water stations and the finish-line "
            "celebration. Corporate teams are welcome."
        ),
        location="Jal Mahal promenade, Amer Road, Jaipur, Rajasthan",
        days_from_now=41,
        weekday=6,
        start=(6, 30),
        duration_hours=3,
        tags=("fundraising", "events", "rajasthan"),
        capacity=None,
        image="/static/img/scenes/parents-meeting.svg",
        image_alt="Parents sit together on a durrie listening to a teacher share their children's progress.",
    ),
    EventSeed(
        slug="library-corner-inauguration-bikaner",
        title="Library corner inauguration, Bikaner",
        summary="Opening our 50th library corner, with 300 new books in Hindi, English and Rajasthani.",
        body=(
            "We opened our 50th library corner at the Napasar centre. Children chose the first "
            "50 books themselves from a shortlist of 200.\n\n"
            "Thank you to the 34 volunteers who sorted, labelled and covered every book."
        ),
        location="Akshar learning centre, Napasar, Bikaner, Rajasthan",
        days_from_now=-18,
        weekday=None,
        start=(10, 0),
        duration_hours=2,
        tags=("library", "events", "rajasthan"),
        image="/static/img/scenes/library-shelf.svg",
        image_alt="A colourful bookshelf with picture books in Hindi, English and Santhali.",
    ),
    EventSeed(
        slug="monsoon-book-drive",
        title="Monsoon book drive",
        summary="Collection points across Jaipur and Ranchi gathered 4,200 children's books for our centres.",
        body=(
            "Over three weekends, families, schools and offices donated 4,200 books. Volunteers "
            "sorted them by reading level so each centre received a balanced set."
        ),
        location="Collection points in Jaipur and Ranchi",
        days_from_now=-62,
        weekday=None,
        start=(10, 0),
        duration_hours=6,
        tags=("library", "fundraising", "events"),
        image="/static/img/scenes/library-shelf.svg",
        image_alt="A colourful bookshelf with picture books in Hindi, English and Santhali.",
    ),
    EventSeed(
        slug="annual-impact-meet",
        title="Annual impact meet",
        summary="Teachers, parents, donors and district officials reviewed a year of learning data together.",
        body=(
            "We shared our full learning assessment results, including the centres that did not "
            "improve and what we're changing there. Read the summary on our blog."
        ),
        location="Akshar regional office, Jaipur, Rajasthan",
        days_from_now=-110,
        weekday=None,
        start=(11, 0),
        duration_hours=4,
        tags=("events", "mentoring"),
        image="/static/img/scenes/parents-meeting.svg",
        image_alt="Parents sit together on a durrie listening to a teacher share their children's progress.",
    ),
]


POSTS: list[PostSeed] = [
    PostSeed(
        slug="how-meena-learned-to-read-in-90-days",
        title="How Meena learned to read in 90 days",
        excerpt="At ten, Meena could recognise only a handful of letters. Three months in a reading group changed that.",
        body="""When Meena joined our centre in Sheo block last July, she was ten years old and in Class 4. She could recognise eight letters of the Hindi alphabet and could not read a single word.

Her teacher, Lalita, placed her in the "letters" group after a five-minute assessment. In a normal classroom Meena would have been taught from the Class 4 textbook. In our centre, she was taught exactly what she needed next.

## What the 90 days looked like

- **Weeks 1 to 3:** letter sounds, five new letters a week, using picture cards and songs
- **Weeks 4 to 7:** joining letters into two- and three-letter words, reading them aloud in pairs
- **Weeks 8 to 12:** short paragraphs from our graded readers, then simple stories

Every day ended with ten minutes of "reading to a buddy", where an older child listened to Meena read and helped with tricky words.

> "She started reading the signs on the bus. Then she started correcting her brother." Meena's mother, Sunita

## Why it worked

Nothing about this is magic. It is the same approach that research on "teaching at the right level" has supported for years: assess, group by level, teach to that level, and reassess often. What makes it work in practice is a teacher who has the time and training to do it, and a group small enough for every child to read aloud every day.

In October, Meena moved to the "story" group. She now borrows two books a week from the library corner. Her favourite is about a girl who builds a bicycle.

Meena's story is one of 12,400. If you want to help the next child in the "letters" group, a monthly gift of ₹1,000 funds evening classes for five children.""",
        author="Lalita Choudhary",
        author_role="Teacher fellow, Barmer",
        tags=("literacy", "stories", "rajasthan"),
        days_ago=6,
        image="/static/img/scenes/reading-circle.svg",
        image_alt="Five children sit in a circle on a mat under a large tree, each holding an open book.",
    ),
    PostSeed(
        slug="teaching-at-the-right-level",
        title="Teaching at the right level: why we group children by skill, not age",
        excerpt="A Class 5 classroom can hold children reading at Class 1 and Class 6 levels. Here's how we handle that.",
        body="""Walk into any rural primary classroom and you will find a huge range of skill. In one Class 5 group we assessed last year, children's reading levels ranged from "cannot identify letters" to "can read a Class 5 textbook fluently".

A teacher following the textbook has to pick one level to teach to. Usually that's the textbook level, and the children who are furthest behind fall further behind every week.

## How our grouping works

At the start of each term, every child takes a short one-to-one reading and maths assessment. It takes about five minutes. Children are then grouped into one of five levels:

1. Beginner: recognises few or no letters
2. Letters: recognises most letters
3. Words: reads simple words
4. Paragraph: reads a short paragraph
5. Story: reads a full story with understanding

Groups are fluid. A child can move up any week, and teachers reassess informally every fortnight.

## What it is not

Grouping by level is not "streaming" children permanently. Our groups exist only during the two-hour centre session; children stay with their age group in school. And because groups change constantly, being in the beginner group is a starting point, not a label.

## The evidence

This approach builds on a large body of research on "teaching at the right level" in India and Africa, including several randomised evaluations. Our own data is less rigorous but encouraging: last year, 71% of children who started in the bottom two levels moved up at least two levels by the end of the year.

We publish our assessment tools so other organisations can use them. Write to us through the contact page if you'd like a copy.""",
        author="Ananya Iyer",
        author_role="Head of Learning and Research",
        tags=("pedagogy", "literacy", "teachers"),
        days_ago=19,
        image="/static/img/scenes/teacher-training.svg",
        image_alt="A teacher stands at a blackboard explaining letters to a group of trainee teachers.",
    ),
    PostSeed(
        slug="inside-our-teacher-fellowship",
        title="Inside our Teacher Fellowship: 40 days that change a classroom",
        excerpt="Our fellows are young women from the villages they teach in. Here's what their training looks like.",
        body="""Every one of our 640 teachers was trained through the Akshar Teacher Fellowship. Most are women between 19 and 26, from the same villages as the children they teach, and most are the first in their families to finish college.

## The 40 days

The fellowship begins with 40 days of residential training, spread over two months so fellows can keep up with home responsibilities.

- **Days 1 to 10:** how children learn to read, and how to assess where a child is
- **Days 11 to 25:** classroom practice with real children, filmed and reviewed with a coach
- **Days 26 to 35:** maths, library sessions and running parent meetings
- **Days 36 to 40:** safeguarding, record keeping and planning the first month of a centre

## After training

Training is the start, not the end. Every fellow gets a coaching visit each month. Coaches observe a full session, then sit with the fellow to plan one specific change for the next month. Small, specific feedback works better than long lists.

Fellows receive a monthly stipend and meet in cluster groups of ten every quarter to share what is working.

## Where fellows go next

About a third of our fellows stay for three years or more and become coaches themselves. Others go on to government teaching jobs, nursing and further study. Pooja, from the 2023 Gumla cohort, put it this way:

> "Before the fellowship I was shy to speak in front of my own family. Now I run meetings with 40 parents."

Applications for the 2027 cohort open soon. Come to our open house in Ranchi to learn more.""",
        author="Rahul Soren",
        author_role="Director, Jharkhand Programmes",
        tags=("teachers", "fellowship", "jharkhand"),
        days_ago=33,
        image="/static/img/scenes/hero.svg",
        image_alt="A teacher reads aloud to a group of children sitting on mats in a village courtyard.",
    ),
    PostSeed(
        slug="keeping-girls-in-school-after-class-8",
        title="Keeping girls in school after Class 8",
        excerpt="The move from Class 8 to Class 9 is when many rural girls leave school. Our scholarship programme targets that year.",
        body="""In the villages where we work, the jump from Class 8 to Class 9 often means a new school, further away, with higher costs. It is the year many girls leave.

Since 2022 our girls' scholarship programme has supported 1,100 girls through that transition. Three years on, 92% of them are still in school.

## What the programme provides

- **A bicycle**, because distance is the most common reason families give for stopping a daughter's education
- **A scholarship** of ₹6,000 a year for fees, uniform and books, paid in instalments linked to attendance
- **A mentoring circle** of 8 to 10 girls that meets every fortnight with a trained woman mentor
- **Parent meetings** each term, where we share the girl's progress and talk through concerns

## What we have learned

The bicycle matters more than we expected. In our end-of-year survey, 64% of girls named it as the single biggest help.

Mentoring circles are the part girls talk about most. Circles cover practical topics (exam preparation, managing money, health) but the real value is a group of peers who expect each other to stay in school.

## What we're changing

Our first cohort taught us that support cannot stop at Class 10. This year we are piloting help with Class 11 subject choices and college applications for 150 girls.

Women volunteers can mentor a circle, in person or online. Visit our volunteer page to sign up.""",
        author="Rahul Soren",
        author_role="Director, Jharkhand Programmes",
        tags=("girls-education", "scholarships", "jharkhand"),
        days_ago=47,
        image="/static/img/scenes/girls-football.svg",
        image_alt="Girls in school uniforms play football on a dusty field at sunset.",
    ),
    PostSeed(
        slug="what-a-1000-rupee-donation-buys",
        title="What a ₹1,000 donation actually buys",
        excerpt="We break down exactly where a ₹1,000 gift goes, down to the snacks.",
        body="""Donors often ask us: what does my money actually do? Here is an honest breakdown of a ₹1,000 donation, based on last year's audited accounts.

## The breakdown

| Where it goes | Amount |
| --- | --- |
| Learning centres and teacher stipends | ₹620 |
| Teacher training and coaching | ₹140 |
| Books, materials and digital kits | ₹100 |
| Assessment and research | ₹50 |
| Fundraising | ₹50 |
| Administration | ₹40 |

In practice, ₹1,000 funds about one month of evening classes for five children: their teacher's time, a daily snack, workbooks and a share of the library.

## Why we spend money on "overheads"

Nine paise of every rupee goes to fundraising and administration. We could make that number smaller by cutting audits, finance staff and donor reporting, but those are exactly the things that let us tell you where your money went.

Assessment and research also look like overhead, but without them we would not know which centres are working and which need help.

## Monthly giving

Monthly gifts are the most useful kind for us because they let us commit to teacher stipends a year in advance. Even ₹500 a month makes a real difference to how we plan.

Our full audited accounts are published every September.""",
        author="Imran Qureshi",
        author_role="Finance and Compliance Lead",
        tags=("transparency", "donors"),
        days_ago=61,
        image="/static/img/scenes/parents-meeting.svg",
        image_alt="Parents sit together on a durrie listening to a teacher share their children's progress.",
    ),
    PostSeed(
        slug="digital-literacy-without-reliable-internet",
        title="Digital literacy without reliable internet",
        excerpt="Most of our centres have patchy power and no broadband. Here's how we built digital corners that work anyway.",
        body="""When we started planning digital corners in 2023, the obvious idea was tablets with learning apps. The obvious problem: most of our centres have unreliable power and no broadband.

## What we built

Each digital corner has:

- **Four rugged tablets** charged by a small solar panel and a battery pack
- **Offline content only**: graded reading apps, maths games and Scratch for coding, loaded once a term from a laptop
- **A lockable steel box** that doubles as a charging station

Nothing in the kit depends on a live internet connection. Teachers sync usage logs once a month when they visit the block office.

## What children actually do

The digital corner is 20 minutes of a two-hour session, in pairs. Pairing was a deliberate choice: children explain things to each other, and four tablets serve a group of eight.

Usage logs showed something we didn't expect. The most popular app is not a game but a reading app that reads a story aloud and highlights each word. Children replay the same stories many times, which is exactly what early readers need.

## What went wrong

Our first battery packs failed in the Barmer heat. We switched to a different supplier and moved the boxes away from tin roofs. Two kits were damaged in the monsoon before we added waterproof bags.

## What's next

We're launching Code Clubs this year, starting in Jaipur district. If you work in tech and want to help, come to our Code Club launch weekend.""",
        author="Ananya Iyer",
        author_role="Head of Learning and Research",
        tags=("digital", "technology", "rajasthan"),
        days_ago=78,
        image="/static/img/scenes/digital-corner.svg",
        image_alt="Two children share a tablet at a low table while a third points at the screen.",
    ),
    PostSeed(
        slug="what-we-learned-from-our-learning-assessments",
        title="What we learned from our 2025-26 learning assessments",
        excerpt="We assessed 11,800 children three times last year. Most improved. Some centres did not, and we want to explain why.",
        body="""Every year we assess every child in our centres three times: at the start, middle and end of the year. Here is what the 2025-26 data showed.

## The headline

- **11,800 children** were assessed at both the start and the end of the year
- **68%** moved up at least one reading level
- **41%** moved up two levels or more
- **Children who attended at least 70% of sessions** were twice as likely to move up two levels

## The centres that did not improve

In 14 of our 172 centres, fewer than a third of children moved up a level. When we visited, we found three common problems: teacher turnover in the middle of the year, centres that started late after the monsoon, and two centres where sessions regularly ran short.

We are now adding a second coaching visit each month for centres that stall in the mid-year assessment, rather than waiting for the end of the year.

## Limits of our data

Our assessments are run by our own teachers, which can bias results upwards. This year an independent team re-assessed a random 10% sample of children, and their results were within 4 percentage points of ours. We will keep doing that check every year.

## What we'll publish

We publish the full centre-level results, including the centres that did badly. We think donors, parents and district officials should see the same numbers we see.""",
        author="Ananya Iyer",
        author_role="Head of Learning and Research",
        tags=("impact", "data", "literacy"),
        days_ago=96,
        image="/static/img/scenes/reading-circle.svg",
        image_alt="Five children sit in a circle on a mat under a large tree, each holding an open book.",
    ),
]
