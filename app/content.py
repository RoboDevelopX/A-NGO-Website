"""Static page copy for the homepage and About page.

Kept as plain data (not in the database) because it changes rarely and is edited by
developers. Events and blog posts, which change often, live in the database instead.
All people, places and numbers are fictional placeholders.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Stat:
    value: int
    suffix: str
    label: str


@dataclass(frozen=True)
class Programme:
    icon: str
    title: str
    text: str


@dataclass(frozen=True)
class Image:
    src: str
    alt: str
    caption: str


@dataclass(frozen=True)
class Testimonial:
    quote: str
    name: str
    role: str
    image: str
    image_alt: str


@dataclass(frozen=True)
class Milestone:
    year: str
    title: str
    text: str


@dataclass(frozen=True)
class TeamMember:
    name: str
    role: str
    bio: str
    image: str


@dataclass(frozen=True)
class FundLine:
    label: str
    percent: int
    detail: str


IMPACT_STATS = [
    Stat(12400, "", "children learning in our centres this year"),
    Stat(186, "", "community learning centres in 2 states"),
    Stat(640, "", "local teachers trained since 2016"),
    Stat(92, "%", "of our girls still in school three years on"),
]

PROGRAMMES = [
    Programme(
        "book",
        "Community learning centres",
        "Two hours every evening, six days a week. Children are grouped by reading level, not "
        "age, so nobody is left behind and nobody is bored.",
    ),
    Programme(
        "teacher",
        "Teacher fellowship",
        "We recruit young women from the same villages, train them for 40 days and coach them "
        "every month. Most of our teachers are the first in their family to finish college.",
    ),
    Programme(
        "girl",
        "Girls stay in school",
        "Scholarships, bicycles and mentoring circles for girls moving from Class 8 to Class 9, "
        "the year most rural girls drop out.",
    ),
    Programme(
        "library",
        "Libraries and digital corners",
        "A shelf of 300 books in three languages and a solar-powered tablet kit in every centre, "
        "loaded with offline learning apps.",
    ),
]

GALLERY = [
    Image(
        "/static/img/scenes/reading-circle.svg",
        "Five children sit in a circle on a mat under a large tree, each holding an open book.",
        "Evening reading circle, Barmer",
    ),
    Image(
        "/static/img/scenes/teacher-training.svg",
        "A teacher stands at a blackboard explaining letters to a group of trainee teachers.",
        "Teacher fellowship training, Ranchi",
    ),
    Image(
        "/static/img/scenes/digital-corner.svg",
        "Two children share a tablet at a low table while a third points at the screen.",
        "Solar-powered digital corner, Gumla",
    ),
    Image(
        "/static/img/scenes/girls-football.svg",
        "Girls in school uniforms play football on a dusty field at sunset.",
        "Saturday football and life-skills camp",
    ),
    Image(
        "/static/img/scenes/library-shelf.svg",
        "A colourful bookshelf with picture books in Hindi, English and Santhali.",
        "Library corner, Bikaner",
    ),
    Image(
        "/static/img/scenes/parents-meeting.svg",
        "Parents sit together on a durrie listening to a teacher share their children's progress.",
        "Monthly parents' meeting, Jaisalmer",
    ),
]

TESTIMONIALS = [
    Testimonial(
        "Last year my daughter could not read the name of her own village on the bus. Now she "
        "reads the newspaper to her grandfather every morning.",
        "Sunita Devi",
        "Parent, Barmer, Rajasthan",
        "/static/img/people/avatar-1.svg",
        "Portrait of Sunita Devi",
    ),
    Testimonial(
        "The fellowship taught me how to teach a child who is three levels behind without "
        "making her feel small. I use that every single day.",
        "Pooja Oraon",
        "Teacher fellow, 2023 cohort, Gumla",
        "/static/img/people/avatar-2.svg",
        "Portrait of Pooja Oraon",
    ),
    Testimonial(
        "I volunteer two Saturdays a month. Seeing a child finish her first full storybook is "
        "the best part of my week.",
        "Arjun Mehta",
        "Volunteer and software engineer, Jaipur",
        "/static/img/people/avatar-3.svg",
        "Portrait of Arjun Mehta",
    ),
]

HERO_IMAGE = Image(
    "/static/img/scenes/hero.svg",
    "A teacher reads aloud to a group of children sitting on mats in a village courtyard.",
    "",
)

VALUES = [
    ("Children first", "Every decision starts with what a child in our centre needs next."),
    (
        "Local leadership",
        "Our teachers come from the villages they teach in, and so do 70% of our staff.",
    ),
    (
        "Radical transparency",
        "We publish audited accounts and learning results every year, good or bad.",
    ),
    ("Learning from evidence", "We test children every term and change what is not working."),
]

PROBLEM_POINTS = [
    "Large national surveys of rural schools, such as the ASER reports, have repeatedly found "
    "that only around half of children in Class 5 can read a Class 2 level text.",
    "Children who fall behind early rarely catch up: classrooms move at the pace of the "
    "textbook, not the child.",
    "Girls are the first to leave when the nearest secondary school is far away or money is tight.",
]

APPROACH_STEPS = [
    (
        "Teach at the right level",
        "A five-minute assessment places each child in a reading group. Groups change as children improve.",
    ),
    (
        "Hire and train local teachers",
        "Fellows from the community get 40 days of training, a monthly coaching visit and a fair stipend.",
    ),
    (
        "Bring parents in",
        "Monthly meetings show parents exactly what their child can now read, in plain language.",
    ),
    (
        "Measure and adapt",
        "Every child is assessed three times a year. Centres that stall get extra coaching support.",
    ),
]

MILESTONES = [
    Milestone(
        "2014", "First centre opens", "22 children, one teacher and a borrowed courtyard in Barmer."
    ),
    Milestone(
        "2016",
        "Teacher fellowship begins",
        "Our first cohort of 18 local women completes training.",
    ),
    Milestone("2018", "Expansion to Jharkhand", "40 new centres in Gumla and Khunti districts."),
    Milestone(
        "2020",
        "Learning through lockdown",
        "Doorstep classes and printed worksheets reach 6,000 children.",
    ),
    Milestone(
        "2022", "100th learning centre", "And our first girls' scholarship cohort of 250 students."
    ),
    Milestone(
        "2024", "Digital corners", "Solar tablet kits with offline apps arrive in 50 centres."
    ),
    Milestone(
        "2026",
        "12,400 children",
        "186 centres across 9 districts, with 640 teachers trained so far.",
    ),
]

TEAM = [
    TeamMember(
        "Kavita Rathore",
        "Founder and Executive Director",
        "Former government school teacher from Barmer who started the first centre in her own courtyard.",
        "/static/img/people/avatar-4.svg",
    ),
    TeamMember(
        "Rahul Soren",
        "Director, Jharkhand Programmes",
        "Leads 70 centres across Gumla and Khunti and the girls' scholarship programme.",
        "/static/img/people/avatar-5.svg",
    ),
    TeamMember(
        "Ananya Iyer",
        "Head of Learning and Research",
        "Designs our assessments and runs the termly learning data reviews.",
        "/static/img/people/avatar-6.svg",
    ),
    TeamMember(
        "Imran Qureshi",
        "Finance and Compliance Lead",
        "Chartered accountant who makes sure every rupee is accounted for and published.",
        "/static/img/people/avatar-7.svg",
    ),
]

FUNDS_BREAKDOWN = [
    FundLine(
        "Learning centres and teacher stipends",
        62,
        "Rent-free spaces, stipends for 640 teachers, daily snacks",
    ),
    FundLine(
        "Teacher training and coaching",
        14,
        "40-day fellowship training and monthly coaching visits",
    ),
    FundLine("Books, materials and digital kits", 10, "Libraries, workbooks and solar tablet kits"),
    FundLine("Assessment and research", 5, "Termly reading and maths assessments"),
    FundLine("Fundraising", 5, "Donor communications and events"),
    FundLine("Administration", 4, "Audit, compliance and office costs"),
]

# Shown on the homepage and the donate page so donors can see what an amount does.
DONATION_IMPACT = {
    500: "A set of graded readers for one child for a whole year",
    1000: "A month of evening classes for 5 children",
    2500: "One month's stipend support for a teacher fellow",
    5000: "A library corner of 50 new books in three languages",
}
