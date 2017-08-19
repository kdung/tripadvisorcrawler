from bs4 import BeautifulSoup, Comment
import requests
import re



output_file = "tripadvisor_output.csv"
review_counter=0;
url =	"https://www.tripadvisor.com.sg/Attraction_Review-g298162-d320634-Reviews-or{data_offset}-Tokyo_Disneyland-Urayasu_Chiba_Prefecture_Kanto.html"
f = open(output_file, "w")


"""-------------------------------------------------------
Function 1:
Remove non-ascii characters from text string
----------------------------------------------------------"""
def remove_nonascii(text):
	if text is not None:
		#return text.encode("ascii", "ignore").decode("ascii").strip()
		return text.encode("utf-8")
	else:
		return text



"""----------------------------------
Function 2:
Get username using uid 
-------------------------------------"""
def get_username(uid):
	if uid is None:
		return

	response = requests.get("https://www.tripadvisor.com.sg/MemberOverlay?", params={"uid":uid})
	overlay = BeautifulSoup(response.content, "html.parser")
	username = overlay.find("a")["href"]
	return username

"""----------------------------------------
Function 3:
Get user info using username
-------------------------------------------"""
def get_user_info(username):
	if username is None:
		return
	
	response = requests.get("https://www.tripadvisor.com.sg" + username)
	container = BeautifulSoup(response.content, "html.parser")
	
	print("------------------------------------------------------")
	reviews = container.find("a", {"name":"reviews"}).string
	reviews = re.search("(.*) Review", reviews).group(1)
	print("Reviews: %s" % reviews)
	
	helpful_votes = container.find("a", {"name":"lists"})
	if helpful_votes is None:
		helpful_votes = 0
	else:
		helpful_votes = helpful_votes.string
		helpful_votes = re.search("(.*) Helpful", helpful_votes).group(1)
	print("Helpful vote: %s" % helpful_votes)
	
	travel_style=[]
	tempstyles = container.find_all("div", class_="tagBubble")
	for a_style in tempstyles:
		travel_style.append(a_style.get_text().strip())
	print("Travel style: %s" % travel_style)
	
	points = container.find("div", class_="points").string.strip()
	print("Points: %s" % points)
	
	
	level = container.find("div", class_="level")
	if level is None:
		level = 0
	else:
		level = level.find("span").string
	print("Level: %s" % level)
	
	badges = container.find_all("div", class_="badgeItem")
	the_badges = []
	for a_badge in badges:
		the_badges.append(a_badge.get_text())
		print("Badge: %s" % a_badge.get_text())
	
	
	f.write(str(reviews)      + "\t" + str(helpful_votes) + "\t"
				+ str(travel_style) + "\t" + str(points)        + "\t"
				+ str(level)        + "\t"
				+ str(the_badges)   + "\n"
				)
	
	print("------------------------------------------------------")
	
	

	
	

"""-----------------------
Function 4:
Process page
--------------------------"""
def process_page(url):
	if url is None:
		return
	
	print("Processing %s" % url)
	
	# Step 1: 
	html = requests.get(url)
	soup = BeautifulSoup(html.content, "html.parser")
	
	# Step 2: Get the review_id
	review_ids = soup.find_all("div", class_="reviewSelector")
	review_id_list = list()
	for a_reviewid in review_ids:
		review_id_list.append(a_reviewid["data-reviewid"])
	#print(review_id_list)
	
	# Step 3: Convert review_id_list to commas seperated payload json
	payload = ",".join(review_id_list)
	payload = {
		"reviews": payload
	}
	#print("Payload: %s\n" % payload)
	
	# Step 4: To expand out "More" so that the whole review can be seen
	r = requests.post(
		url='https://www.tripadvisor.com.sg/OverlayWidgetAjax?Mode=EXPANDED_HOTEL_REVIEWS&metaReferer=Attraction_Review',
		data=payload,
		headers={
			'X-Requested-With': 'XMLHttpRequest'
		}
	)
	
	# Step 4: Get the new url
	soup = BeautifulSoup(r.content, "html.parser")
		
	
	container = soup.find_all("div", class_="review")
	
	for a_container in container:
		global review_counter
		review_counter = review_counter+1;
		print("S/N: %d" % review_counter)
			
		screen_name = a_container.find("span", class_="scrname").string
		screen_name = remove_nonascii(screen_name)
		print("Screen name: %s" % screen_name)
		
		user_location = a_container.find("span", class_="userLocation")
		if (user_location) is None:
			user_location = "None"
		else:
			user_location = remove_nonascii(user_location.string)
		print("User location: %s" % user_location)
		
		
		
		# Get rating: 	<span class="ui_bubble_rating bubble_50"></span>
		rating = a_container.find("span", class_="ui_bubble_rating")["class"][1][7]
		print("Rating: %s" % rating)
		
		rating_date = a_container.find("span", class_="ratingDate")["title"]
		print("Rating date: %s" % rating_date)
		
		title = remove_nonascii(a_container.find("span", class_="noQuotes").string)
		print("Title: %s" % title)
	
		
		
		entry = remove_nonascii(a_container.find("p", class_="partial_entry").get_text())
		print("Entry: %s" % entry)
		
		
		
		uid = a_container.find("div", class_="memberOverlayLink")
		if uid is None:
			continue
		uid = uid["id"]	
		uid = re.search("UID_(.*)-SRC*", uid).group(1)
		print("uid: %s" % uid)
		username = get_username(uid)
		print("username: %s" % username)
		
		f.write(str(review_counter) + "\t" + str(screen_name) + "\t"
					+ str(user_location)  + "\t" + str(rating)      + "\t"
					+ str(rating_date)    + "\t" + str(title)       + "\t"
					+ str(entry)          + "\t"
					+ str(uid)            + "\t" + str(username)    + "\t"
					)
		
		get_user_info(username)
		print("")

"""-------------------------------------------------
Function 5:
[1] Find out last page offset
[2] Loop through all pages till the last page
----------------------------------------------------"""
def loop_pages(url):
	# Step 1: Find out the last page offset
	data_offset=0
	current_url = url.format(data_offset = 0)
	
	html = requests.get(current_url)
	soup = BeautifulSoup(html.content, "html.parser")
	
	last_data_offset = int(soup.find("span", class_="last").get("data-offset"))
	print(last_data_offset)
	
	# Step 2: Loop through the pages till the last page
	for current_offset in range(0, last_data_offset+1, 10):
		current_url = url.format(data_offset = current_offset)
		process_page(current_url)
		
		
"""----------------------
Start of main program
-------------------------"""
import time, sys
try:
	loop_pages(url)
except KeyboardInterrupt:
	f.close()
	print("\t\tFile closed successfully. Bye.")
except:
	f.close()
	print("\t\tException caught. File closed successfully. Bye.")
	
	print(sys.exc_info()[0])
	raise
	
	



	
	