def make_hand(index=False, middle=False, ring=False, pinky=False, thumb=False, pinch=False, dx=0.0, dy=0.0):
    lm = [(0.0, 0.0)] * 21
    lm[0] = (0.5, 0.9)
    bases = {"index": (5, 0.42, 0.65, index), "middle": (9, 0.50, 0.63, middle),
             "ring": (13, 0.58, 0.65, ring), "pinky": (17, 0.65, 0.68, pinky)}
    for _, (i, x, y, ext) in bases.items():
        pts = ([(x, y), (x, y - 0.10), (x, y - 0.17), (x, y - 0.23)] if ext
               else [(x, y), (x, y - 0.06), (x, y - 0.01), (x, y + 0.04)])
        lm[i:i + 4] = pts
    if thumb:
        lm[1:5] = [(0.42, 0.85), (0.36, 0.78), (0.31, 0.72), (0.27, 0.67)]
    else:
        lm[1:5] = [(0.42, 0.85), (0.40, 0.78), (0.44, 0.74), (0.47, 0.72)]
    if pinch:
        lm[4] = (0.47, 0.72)
        lm[8] = (0.49, 0.72)
    return [(x + dx, y + dy) for x, y in lm]
