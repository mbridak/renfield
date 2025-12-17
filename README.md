# renfield

![CLI Screenshot](https://github.com/mbridak/renfield/raw/refs/heads/main/renfield2.svg)

<center>^ I was bored. Kinda reminds me of Sun Microsystems. ^</center>

## Danger

This will be the Not1MM contest data aggregation server. It's currently not feature complete.

## Recent Changes

- [25-12-16] Add score widget.
- [25-10-5] Add Dupe checking.
- [25.9.26] Add support to get serial numbers from the server.
- [25.9.25] Got it generating Cabrillo files.
  - Group chat
  - Current User/Band/Mode
  - QSO by band/mode/points

## The Idea

Renfield is an amateur radio contest contact aggregation server for [Not1MM](https://github.com/mbridak/not1mm). It uses [Textual](https://textual.textualize.io) for rendering the interface. This provides the user with either a CLI or a web interface depending on how it is launched.

The client(s) Not1MM and the server Renfield talk to each other over a UDP Multicast network connection. There is no file sharing or network file access. The Not1MM clients and Renfield each maintain their own database. As contacts are made they are stored in Not1MM's local database. That record is marked 'Dirty' and a UDP message is sent out. Once Renfield gets the message and saves it's copy, Renfield sends a response message to confirm. The Not1MM client gets the confirmation and clears the 'Dirty' flag on the record. Not1MM keeps track of the messages it has sent out. If it doesn't get a reply either because Renfield didn't get it or Not1MM didn't get the confirmation message, Not1MM will just retry every 30 seconds until it does. Each contact has a [UUID v4](https://en.wikipedia.org/wiki/Universally_unique_identifier) tag to prevent any duplicate records.

If Renfield should crash and burn, or the PC/device it is running on should catch fire. You can spin up another instance of Renfield, then have the Not1MM clients mark all their contacts as dirty, and they will re-stream all their contacts to the new server. Eventually I'll make that reciprocal. Where if a Not1MM client were to fail, it will be able to ask Renfield to send all it's contacts back.

## Things that need doing

- [x] Make a stupid logo.
- [x] Discover which contest is being run.
- [x] Handle QSO CRUD operations.
- [x] Show Points, Mults and Score.
- [x] Show some basic band/qso/point statistics.
- [x] Chat functions (handled by the clients)
- [x] Manage giving out serial numbers.
- [x] Generate a Cabrillo file.
- [x] Indicate Dupes when queried.
- [ ] Reverse feed QSO's back to a client if requested.

## Installation

You can install\update renfield easily with [uv](https://docs.astral.sh/uv/):

```sh
uv tool install renfield@latest
```

## Running renfield

### CLI interface

You can run renfield and have it's interface displayed directly in the terminal with:

```sh
# renfield
```

![CLI Screenshot](https://github.com/mbridak/renfield/raw/refs/heads/main/pic/renfield_cli.svg)

### Run as a web server

You can run renfield as a web server with:

```sh
# textual serve renfield
```

You'll see this message:

![CLI Screenshot](https://github.com/mbridak/renfield/raw/refs/heads/main/pic/renfield_ss_terminal.png)

You or others on your network can connect to the web interface on port 8000

![CLI Screenshot](https://github.com/mbridak/renfield/raw/refs/heads/main/pic/renfield_ss_web.png)

### Run from the source tree

> textual serve \_\_main\_\_.py

## Networking

Communication between the clients and the server happens on UDP multicast port 2239 by default. Depending on your linux distribution you may need open that port in your firewall on each machine manually. I've retired from the IT field, so I'll leave that as an exercise for you.

## Direct commands

Interacting with the server via it's CLI or web interface is limited.

 - 'q' Quits the program.
 - 'R' Resets/Wipes the database.
 - 'Z' Zero out the SN server.
 - 'c' Generates a Cabrillo file for whatever contest is active.
