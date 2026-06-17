# A SEV-0 Walkthrough

This is a realistic example of how `fffuuu` fits into an incident response
at 3am — when the tools you'd normally use to find help are themselves
struggling.

---

## The scenario

It's **3:07am**. You're on-call. Your monitoring fires: the API gateway is
returning 503s across all regions. You open your laptop.

Slack is slow — the company's SSO provider is also having issues, so half
your internal tools are broken. PagerDuty loaded but the escalation links
are timing out. You need a human being on the phone in the next two minutes.

---

## Step 1: Who's on-call right now?

You don't remember. You were asleep four minutes ago.

```
$ fck oncall
```

```
████████████████████████████████████████████████████████████████████████
  ███████ ███████ ██    ██     ██████
  ██      ██      ██    ██    ██    ██
  ███████ █████   ██    ██    ██    ██
       ██ ██       ██  ██     ██    ██
  ███████ ███████   ████       ██████
████████████████████████████████████████████████████████████████████████

── ON-CALL NOW (1 person) ───────────────────────────────────────────────

Grace Hopper  [ON-CALL]
  role :  SRE Lead   team: platform
  phone:  +39-333-000-0001
  slack:  @grace
```

Phone number. Right there. You call Grace.

---

## Step 2: Grace doesn't pick up

It happens. The 503s look like they could be a routing issue — you need
the networking team.

```
$ fck team networking
```

```
── team: NETWORKING ─────────────────────────────────────────────────────

Dennis Ritchie
  role :  SRE   team: networking
  phone:  +39-333-000-0002
  slack:  @dennis

Ken Thompson
  role :  Principal SRE   team: networking
  phone:  +39-333-000-0003
  slack:  @ken
```

You call Dennis. He picks up.

---

## Step 3: Dennis asks you to loop in the database lead

You don't know her number off the top of your head.

```
$ fck find db
```

```
── Results for 'db' (1) ─────────────────────────────────────────────────

Ada Lovelace
  role :  DB Lead   team: data
  phone:  +39-333-000-0004
  slack:  @ada
```

You three are now on a call within five minutes of the alert firing.

---

## Step 4: You need to escalate further

Halfway through the incident you realise you need a vendor escalation contact.
You check notes:

```
$ fck find escalation -v
```

```
── Results for 'escalation' (1) ─────────────────────────────────────────

Ken Thompson
  role :  Principal SRE   team: networking
  phone:  +39-333-000-0003
  slack:  @ken
  notes:  Wake Ken only for full DC loss. Has vendor escalation contacts
          for Cloudflare, AWS, and the dark fibre provider.
```

The `-v` flag is the one that earns its keep here — that note about vendor
contacts would have taken three Confluence searches to find otherwise.
If Confluence were up.

---

## Step 5: Incident resolved — rotate on-call for the next shift

```
$ fck set-oncall dennis --replace
[fff] Marked Dennis Ritchie as ON-CALL
```

---

## What just happened

Five commands. All local. All instant. No browser, no login, no network call
to an external service.

That is the entire point of this tool: during a SEV-0 the services you rely
on to coordinate a response are often part of the blast radius. Your contact
directory should not be.
