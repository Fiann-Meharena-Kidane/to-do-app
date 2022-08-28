import os

link_start = "https://quickchart.io/chart?c={type:%27progressBar%27,data:{datasets:[{data:["
link_end = "]}]}}"
percentage=str(90)

print(link_start+percentage+link_end)
