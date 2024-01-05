<p align="center">
    <a href="" rel="nooperner">
    <img width=200px height=200px src="logo.png" alt="Tailfin Logo"></a>
</p>

<h3 align="center">Tailfin</h3>

---

<p align="center">A self-hosted digital flight logbook</p>

## Table of Contents

+ [About](#about)
+ [Getting Started](#getting_started)
+ [Configuration](#configuration)
+ [Usage](#usage)
+ [Roadmap](#roadmap)

## About <a name="about"></a>

Tailfin is a digital flight logbook designed to be hosted on a personal server, computer, or cloud solution. This is the
API segment and can be run independently. It is meant to be a base for future applications, both web and mobile.

I created this because I was disappointed with the options available for digital logbooks. The one provided by
ForeFlight is likely most commonly used, but my proclivity towards self-hosting drove me to seek out another solution.
Since I could not find any ready-made self-hosted logbooks, I decided to make my own.

## Getting Started <a name="getting_started"></a>

### Prerequisites

- python 3.11+
- mongodb 7.0.4

### Installation

1. Clone the repo

```
$ git clone https://git.github.com/azpsen/tailfin-api.git
$ cd tailfin-api
```

2. (Optional) Create and activate virtual environment

```
$ python -m venv tailfin-env
$ source tailfin-env/bin/activate
```

3. Install python requirements

```
$ pip install -r requirements.txt
```

4. Configure the database connection

The default configuration assumes a running instance of MongoDB on `localhost:27017`, secured with username and
password `tailfin-api` and `tailfin-api-password`. This can (and should!) be changed by
modifying `.env`, as detailed in [Configuration](#configuration). Note that the MongoDB instance must be set up with
proper authentication before starting the server. I hope to eventually release a docker image that will simplify this
whole process.

5. Start the server

```
$ python app.py
```

## Configuration <a name="configuration"></a>

To configure Tailfin, modify the `.env` file. Some of these options should be changed before running the server. All
available options are detailed below:

`DB_URI`: Address of MongoDB instance. Default: `localhost`
<br />
`DB_PORT`: Port of MongoDB instance. Default: `27017`
<br />
`DB_NAME`: Name of the database to be used by Tailfin. Default: `tailfin`

`DB_USER`: Username for MongoDB authentication. Default: `tailfin-api`
<br />
`DB_PWD`: Password for MongoDB authentication. Default: `tailfin-api-password`

`REFRESH_TOKEN_EXPIRE_MINUTES`: Duration in minutes to keep refresh token active before invalidating it. Default:
`10080` (7 days)
<br />
`ACCESS_TOKEN_EXPIRE_MINUTES`: Duration in minutes to keep access token active before invalidating it. Default: `30`

`JWT_ALGORITHM`: Encryption algorithm to use for access and refresh tokens. Default: `HS256`
<br />
`JWT_SECRET_KEY`: Secret key used to encrypt and decrypt access tokens. Default: `please-change-me`
<br />
`JWT_REFRESH_SECRET_KEY`: Secret key used to encrypt and decrypt refresh tokens. Default: `change-me-i-beg-of-you`

`TAILFIN_ADMIN_USERNAME`: Username of the default admin user that is created on startup if no admin users exist.
Default: `admin`
<br />
`TAILFIN_ADMIN_PASSWORD`: Password of the default admin user that is created on startup if no admin users exist.
Default: `change-me-now`

`TAILFIN_PORT`: Port to run the local Tailfin API server on. Default: `8081`

## Usage <a name="usage"></a>

Once the server is running, full API documentation is available at `localhost:8081/docs`

## Roadmap <a name="roadmap"></a>

- [x] Multi-user authentication
- [x] Basic flight logging CRUD endpoints
- [ ] Implement JWT refresh tokens
- [ ] Attach photos to log entries
- [ ] PDF Export
- [ ] Import from other log applications
- [ ] Integrate database of airports and waypoints that can be queried to find nearest
- [ ] GPS track recording
