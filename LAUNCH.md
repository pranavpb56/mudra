# Launch playbook (do this in order)

## Before you build more: validate it works on YOUR machine (day 1)
1. `./setup.sh` then `mudra`. Fix anything that breaks. Tune `smoothing` and `frame_margin` until the cursor feels buttery. **Feel is the product.**
2. Check the name is free: PyPI (`pip install mudra`), GitHub, and the .com/.dev domain. If taken, rename (search/replace "mudra").

## Days 2-5: make the demo irresistible
Shot list (one 20-second vertical video, good light, plain background, screen visible):
1. 0-3s: Hands off keyboard. Caption: "My Mac. No mouse. No keyboard."
2. 3-8s: Point, pinch, drag a window; scroll a long page with peace sign.
3. 8-12s: Palm swipe between two desktops.
4. 12-18s: Shaka + "open notes" ... "search Hyderabad weather".
5. 18-20s: Text: "Open source. Link in bio." + repo name.

Record a screen+webcam version too, convert to a GIF (<8 MB) for the README top: `docs/demo.gif`.

## Days 5-10: polish what people see first
- README top 10 lines + GIF + 3-line install. Nothing else matters as much.
- Add 2-3 plugins people can copy (Spotify control, presentation clicker, "type what I say").
- Tag 10 issues "good first issue" from the roadmap.
- Add a GitHub topic list: `gesture-control`, `mediapipe`, `macos`, `computer-vision`, `whisper`, `accessibility`.

## Launch day (Tue-Thu, ~8-10am US Eastern = evening in India)
- **Show HN**: "Show HN: Mudra – control your Mac with hand gestures and offline voice". First comment: why you built it, how it works, what's rough. Stay online to answer for 4 hours.
- **X / LinkedIn**: the 20s video + 3 lines: what it does, "100% offline", repo link in first reply.
- **Reddit**: r/MacOS, r/opensource, r/computervision, r/Python, r/SideProject. Tailor each post; never paste the same text.
- **Product Hunt**: only after HN/Reddit traction. Needs a gallery and a hunter.
- Reply to every comment and issue in the first 48 hours. That is what turns views into stars and contributors.

## After launch
- Ship a visible release every week for a month (0.2, 0.3...). Momentum compounds.
- Write one blog post: "How I built hand-gesture control in 600 lines of Python."
- Money later: accessibility edition, presentation/stage mode, kiosk/retail license, a hardware-agnostic SDK. Don't think about this until the repo has real users.
