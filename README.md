# SwEng24-GuidewireHomeAlarm

## First Commits

- Avery
- Lance
- Matthew
- Thiago
- Kevin
- Veronika
- Maksym
- Christy

## Week 1

This week we worked on setting everything up, including meetings, getting everyone comfortable on Gitlab, and setting goals for ourselves. We want to make this project stand out from typical alarm systems and other projects so we have a chance of making it to the showcase.

To achieve this, here are some goals/ideas the group has set:

- Target sustainability and simplicity by avoiding using cloud, maybe even track energy usage
- We would really love to get the base of our app done by week 5 (presentations) to set a goal for ourself to actually get out app published
- Create alarm testing feature to ensure its working and allow for a lot of customization for users, so they are able to feel secure
- Time boxed access for guests like cleaners to disable/enable alarm only at certain times, goes along with allowing for multiple users on a single system to have different permissions (maintenance vs admin, etc.)
- Creating our own algorithm for the cybersecurity aspect
- Implement extendable features (or proof of concept) such as cameras, facial recognition, and motion detection

Simply put, we want our project to stand out for usability, sustainability, and simplicity, while also providing features that other alarm systems don't. We would like to take the project as far as we can into the competition.

## Proposed Framework

![image](Images\Framework_1.0.png)

### Notes:

- Open/Close Sensors can be put on windows as well. Also need to keep in mind scalability when introducing more sensors.
- ESP32 will send event states via wifi to our backend server. Backend code will then interpret events (ie. Open or close, which sensors etc)
- For frontend, we will have a web application for Maintenance/Admin and a mobile application for our end users.
- Finally, scalability needs to be kept in mind for multiple homes with multiple end users and ESP32. Also, good to keep in mind when developing that this security system can be easily integrated into a larger security system (Cameras, sensors etc).

## Repository structure

| Part          | Path         | Tech                    |
|---------------|--------------|-------------------------|
| Backend       | `backend/`   | FastAPI, PostgreSQL     |
| Mobile app    | `frontend/`  | Android (Kotlin, Compose) |
| Microcontroller | `microcontroller/` | ESP32, MicroPython |

- **Backend:** `cd backend && py run.py` — API at http://127.0.0.1:5000, docs at `/docs`. See `backend/README.md` and `backend/db/README_SETUP.md`.
- **Frontend:** Android app; open in Android Studio or build with Gradle.
- **Microcontroller:** ESP32 firmware in `microcontroller/src/`; see `microcontroller/notes.md`.

## Proposed Tech Stack

| Layer                              |                 Tech                  | Description                                                                                                                                                                                                                                                           |
| :--------------------------------- | :-----------------------------------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Middleware (ESP32 Microcontroller) |                ESPHome                | Easy to implement API into our backend thats desgined for the ESP32 and can communicate with the device over wifi                                                                                                                                                     |
| Backend                            | FastAPI + PostgreSQL                 | REST API (auth, events, pairing). Run locally; deploy e.g. on Raspberry Pi.                                                                                                                                                                                            |
| Frontend                           | React / JavaScript. Kotlin + Gradle. | For admin/maintenance, we can use a simple web application using React and JavaScript. For end users, we can develop an android app using Kotlin (basically typeScript) and build with gradle.                                                                       |

### Other Tech / Notes

- We can use google oauth to implement creating user accounts and keeping them secure. This will be in frontend and backend. It should be pretty simple then in one home to add user accounts with different roles (ie, owner, resident, maybe neighbour role?)
- We can use firebase for push notifications. This will be in frontend and backend.
- How we are gonna deploy our backend is what we still are kinda undecided on, but for now it's ok because it's easier to have local backend running during dev time.