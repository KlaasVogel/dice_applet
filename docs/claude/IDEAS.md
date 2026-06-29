## IDEA

I want to create a webapplet.

It's a website where student can record their measurements.

It's an experiment to simulate radiactive decay, using dice.
For this activity students are given 100 dice. All of these dice have 2 blue sides, 1 white side and 3 unpainted sides.
They roll all dice and remove all dice with a certain colour on top (these dice are "decayed")
They count all remaining dice and roll again. This process is repeated until all dice are gone.

First run: remove all dice with blue on top.

Second run: remove all dice with white on top.

In a second version of this experminent it requieres 2 students.
Student 1 starts with all the dice. student 2 has none.
Student 1 does the same experiment as described earlier, but instead of removing the dice, he gives all dice with a certain colour to the second student.
Student 2 can now roll his/her dice and removes also the dice of a certain colour. These dice are removed completely. Both students record the amount of dice before each roll.


First run: student 1 donates all dice with blue on top and student 2 removes all dice with white on top

Second run: student 1 donates all dice with white on top and student 2 removes all dice with blue on top.


## APPLET:
functionality website: all text should be default in dutch (except for the animal names)
top corner flags to change language to english or back to dutch.
top corner icon (gear) to display login field
Teacher can login, using a password.
Teacher has a dashboard and can:
	can create classrooms
	overview active and inactive classrooms
	when clicking on one classroom (or after creating a new classroom) a classroomview is opened.
	option to logout

Classroomview:
	displays graph of all measurements of the whole classroom (which are approved by teacher)
	shows a login code (4 or 5 characters) for students to join the classroom
	shows the url to the applet and 2 qr-code (one for site only and one with code to classroom in url) 
	a button to show graph of all measurements all time. (will change graph)
	top corner a small icon (gear) to access config of this classroom. Clicking this gear will open a new tab (or new window) with classroomsettings

Classroomsettings:
	view graph of whole class (can be hidden)
	view data (and graph of each student / group of students)
	data also shows name of student and accesscode
	button/switch to approve data -> will update graph)
	button to lock data + plus label (activated when student requests unlock + red x to deny request) unlocking data also removes request)

Studentview:
	when not logged in, show field to enter classroom or personal code.
	when the ip of the student is recognized from list of active ips: add option to log in as "<name>" 
	
	when logged in using classroom code:
		generate a <name> + logo for student (=animal) we need a list of animal names (english) and icons
		generate a personal (unique) code for the student to re(login) when connection has been lost.
	when logged in, show:
	icon + <name> of student
	the personal code and short instructions to write down the unique code and to share the code when 2 students are working together, so student 2 can access the same workspace.  
	four "tiles" for the students to switch between activities
	When one of the tiles is selected, show:
		a graph
		<placeholder> warning/info that workspace has been locked by teacher + button request unlock) 
		a table to fill in the measurements (at the start about 12 fields, but more fields can be added at the end (plus sign))
		maybe option to add/remove rows in table. 
		a field with the tasks for the pupils.

Graphs:
	label x-axis: worp / throw
	label y-axis: "actieve" dobbelstenen / "active" dice
	dots for all the measurements
	smooth line between the dots
	(for the last 2 activities show 2 lines)
	when hovering the graph with mouse -> 
		show red vertical (thin) line based on horizontal position of the cursor and a thin red horizontal line where the first red line crosses the line of the graph
		show coords of this crossing next to the crossing
		(in the last 2 activities show an extra horizontal line and coords for the second 

## Infrastructure
website url is going to be: www.klaasvogel.nl/natuurkunde/dobbelstenen
I think I want to use p5.js 



	
	 
 	
	
	






