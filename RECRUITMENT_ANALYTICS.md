# Job Portal & Recruitment Analytics (Roll No. A-361)

## Project overview

This coursework project demonstrates how a Django job portal database can be
used to answer recruitment questions with database aggregations. The portal
application is based on the upstream open-source Django Job Portal project
(see its original credits and license in `README.md` and `LICENSE`). The
analytics command and this coursework guide are the additions for the A-361
topic. Keep that distinction when presenting the work.

### Simple explanation (Hinglish)

Ye project employer ko jobs post karne aur candidate ko jobs par apply karne
deta hai. Django models data ko SQLite database mein rakhte hain. Analytics
command unhi records ko group/count karke demand, location, company activity,
application outcome aur salary ka summary print karta hai. Command read-only
hai: report dekhne se source records modify nahi hote.

## Topic entities and how this portal represents them

| Topic entity | Portal model/table concept | Relationship / note |
| --- | --- | --- |
| Candidate | `accounts.User` with employee role | One user can submit many applications. |
| Company | `jobsapp.Company` | A company belongs to an employer user and can post many jobs. |
| Job | `jobsapp.Job` | Each job belongs to a company; it has a location, status and salary fields. |
| Application | `jobsapp.Applicant` | Connects one candidate to one job; a candidate can apply only once per job. |
| Interview | `jobsapp.Interview` | Each interview belongs to an application and records stage, scheduled date and status. |
| Hiring | `jobsapp.Hiring` | One confirmed hire per application; records hire date, optional start date and agreed salary. |

`tags.Tag` linked to `Job` through a many-to-many relation supplies skill
keywords. `categories.Category` records the broader job category.

## How to run

From the project folder, activate the Python environment, install
`requirements.txt`, then run:

```powershell
python manage.py migrate
python manage.py seed_portal_data --jobs 300 --applications 500 --seed 42
python manage.py recruitment_analytics
```

The seed command creates repeatable demo data (seed 42). Running it more than
once can create additional records, so use a fresh development database for a
clean demonstration. Do not run demo seeding against a real/live database.

## Analysis definitions

1. **Demanded skills:** count distinct jobs linked to each tag; sort descending.
2. **Active companies:** count verified companies with at least one published,
   unfilled job. This is an explicit project definition of “active”.
3. **Jobs by location:** count job records for each location string.
4. **Application success rate:** accepted applications divided by all
   applications, multiplied by 100. Accepted is status 2 in the current model.
5. **Hiring rate:** confirmed hires divided by all applications, multiplied by
   100. A `Hiring` row is the evidence of a hire; acceptance alone is not.
6. **Hiring time:** average elapsed days from application creation to confirmed
   hire date for applications with a `Hiring` row.
7. **Salary trends:** average lower and upper salary ranges grouped by currency
   and pay period, so unlike currencies/periods are never combined.

## How to explain the implementation

- `python manage.py recruitment_analytics` invokes a Django management command.
- Interview and confirmed hire records can be entered in Django Admin. Add an
  Interview against an application for each stage; record a Hiring only when
  the application is accepted. The model rejects hires on pending/rejected
  applications and hire dates earlier than the application date.
- Each report section uses QuerySets, which Django translates into SQL queries.
- `Count` performs counts, `Avg` computes salary averages, and `values` groups
  rows by a field. `distinct=True` prevents many-to-many tag joins from counting
  the same job more than once.
- The report shows “No data available” for empty groups rather than inventing
  sample results. Seed demo data first if a populated report is needed.
- This version runs analytics in Django against the configured database
  (SQLite by default). Hadoop, HDFS, Hive and Sqoop are not configured in this
  repository. A later big-data extension could export these tables to HDFS,
  define Hive external tables, run equivalent SQL aggregates, and import
  results for comparison; do not claim that pipeline has run until it is built
  and demonstrated.

## Viva preparation

**Why use `distinct=True` for demanded skills?** A job can join through tags
and the SQL join can produce duplicate job rows. Distinct job counting avoids
inflated demand.

**Why group salary by currency and period?** An annual amount cannot be fairly
averaged with a monthly amount, and values in different currencies are not
comparable without conversion.

**Can we call accepted applications hires?** No. Acceptance means the employer
accepted the application. Only a corresponding `Hiring` record counts as a
confirmed hire in the hiring rate.

**What would you add next?** More interview stages and outcome dates would let
us compare conversion and duration at each recruitment stage. The current model
already records interviews and confirmed hire dates, so its basic hiring rate
and time-to-hire are measurable.
