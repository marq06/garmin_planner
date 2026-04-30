# Garmin Planner
This is a Python program reads a YAML configuration file to create and schedule workouts on Garmin Connect. It remove the needs of manual workout management on the garmin connect web by automating the creation and scheduelling processes in bulk. 

## Motivation
Garmin users would know how much of a pain in the A it is to create and manage workouts on garmin connect, especially when you are following a structured marathon plan. I wrote this Garmin Planner to simplify the planning and scheduling of workouts, so we all can hit our PBs.


## Features

- **Workout Creations**: Create various types of workouts (e.g., intervals, easy runs) with associated details like warmup and cooldown periods on garmin connect.
- **Scheduling**: Scheduling workouts created on garmin connect.
- **Activity Fetcher**: Fetch the latest Garmin Connect activity and display all `INTERVAL_ACTIVE` splits.
  - Includes activity name, start/end time in CET, and split metrics.
  - Supports output formats: `table`, `json`, `csv`, and `compact`.

## Activity Fetcher / Activity API

A new CLI command is available to fetch the latest activity from Garmin Connect and print all `INTERVAL_ACTIVE` split details.

Supported output modes:

- `table`: human-readable table
- `json`: structured JSON object with metadata and splits
- `csv`: CSV rows for splits, with activity metadata appended at the end in an Excel-friendly form
- `compact`: compact text message style output with activity name and CET times

Example usage:

```bash
python -m garmin_planner.fetcher_main --output compact
```

Example CSV output ends with metadata rows like:

```csv
,,Activity Name,Bordeaux - intervals_5x1000
,,Start Time CET,2026-04-30 07:24:55
,,End Time CET,2026-04-30 08:19:30
```

## Input YAML Structure

Your YAML configuration should include the following sections:

1. **User Credentials**:
   - create a `secrets.yaml` file in the `garmin_planner` folder and add your garmin connect credentials
   - ```yaml 
     email: "your@email.com"`
     password: "mySecretPassword"
     ```

2. **Settings**:
   - `deleteSameNameWorkout`: A boolean indicating whether to delete existing workouts with the same name during creation of workout.

3. **Definitions** (optional):
   - A set of predefined values can be used in workout creation, this is optional you can use raw value instead of using this.

4. **Workouts**:
   - Define each workout details for workout creation.
   - Step type keys include: `warmup`, `cooldown`, `interval`, `recovery` and `repeat`.
   - Start / End condition keys include: Lap Button `lap`, Time as `sec` or `min` and Distance in `m`
   - Possible target types include: Heart Rate `@H`, Pace `@P` and custom hear rate range `@X` .

5. **Schedule Plan**:
   - Specify the start date and the sequence of workouts for workout scheduling. 
   - (This will get all the workouts created on garmin connect, schedule them based on the workout name, if the workout is not found on garmin connect it will skip the day)
   - schedule multiple workouts on a single day by separating them with a comma (`,`).
   - For a rest day, write `rest` in the schedule plan. 

### Sample YAML Structure

```yaml
settings:
  deleteSameNameWorkout: true

definitions:
  GA: 6:35-7:00
  Threshold: 5:20-5:45
  VO2MaxP: 3:30-4:00

workouts:
  interval_Vo2Max:
    - warmup: 15min @H(z2)
    - repeat(8):
      - run: 30sec @P($VO2MaxP) # can use definition here or raw value 3:30-4:00
      - recovery: 1200m
    - cooldown: 15min @H(z2)
  ga_30min:
    - warmup: lap
    - run: 30min @X(120-135)
    - cooldown: lap

schedulePlan:
  start_from: 2024-10-08
  workouts: 
    - interval_Vo2Max   # will be scheduled on 2024-10-08
    - ga_5k, ga_30min   # will both be scheduled on 2024-10-09
    - rest              # if no "rest" workout found on garmin connect, skip this day
```

The interval_Vo2Max defined above translate to garmin plan below:
![garmin plan of interval_Vo2Max](image.png)

## Installation

Follow these steps to set up the project locally:

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yeekang-0311/garmin_planner.git

2. **Install dependencies:**
    ```bash
    pip install -r requirements.txt

3. **Run the program:**
    ```bash
    python -m garmin_planner sampleInput.yaml