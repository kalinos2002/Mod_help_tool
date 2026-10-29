Tool what helps you build/create/port mod with AI like claude
Select your project directory [Project main folde (where gradlew is)] -> select downloads ( or folder where you download procided builds form mod) directory
Use tools like Gradle Panel to build/runClient/runServer and create build.log file after succesfull command
After you run gradlew hit "DUMP ERRORS" button to create easy readable file for your AI tool
Upload errors.md to your AI tool and listen what AI want from you, LISTEN CAREFULLY BEACUSE AI CAN ASK FOR OTHER FILES THAN ERRORS.MD
After your AI provide .zip file downlaod it to the same directory and hit "Refresh list" button to reload zip files list in your "downloads" folder.
After that select yopur newest zip hit "EXTRACT AND OVERWRITE STRUCTURE" button, and your project automatically updates, and after that u can hit Gradle Panel again to get new errors or succesfull build!

im providing Python script if u dont trust online resources and .EXE file if u want ot use this on VM or with trust to me
Of you want build your own .EXE file type this where your /pyw file is located and search for exe in libs/<generated_file>.EXE
-> python -m PyInstaller --noconsole --onefile program.pyw

Warning!!! THIS IS ONLY TESTED ON WINDOWS!!!
