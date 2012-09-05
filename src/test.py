import colorsys

colors = []
for h in range(0,3600):
	r, g, b = colorsys.hsv_to_rgb(float(h) / float(3600), 1.0, 1.0)
	rgba = 0xFF000000 + (int(r * 255) << 16) + (int(g * 255) << 8) + int(b * 255)
	colors.append(rgba)
	
for c in colors:
	print(hex(c))

