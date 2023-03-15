# ChimeraX_OpenCommands
 run commands when opening files

### Description
Do you find yourself running the same commands after you open file? Will your fingers fall off if you have to type out `coordset slider #1` two more times? Well, have we got the bundle for you! Introducing OpenCommands, the magical plugin that'll make you feel like a molecular modeling wizard! With OpenCommands, you'll waste less of your precious brainpower on tedious command line instructions.

Simply define your custom commands or Python code, sit back, and let OpenCommands do the rest! Want to generate a molecular surface representation of your opened file? No problem! How about calculating the electrostatic potential of a molecule? Easy-peasy! OpenCommands lets you create commands that do it all.

And the best part? Your commands will be executed automatically whenever you open a file in ChimeraX. It's like having your own personal assistant, but for molecular modeling! With OpenCommands, you'll be free to focus on your research and analysis tasks, without getting bogged down by the nitty-gritty details of command-line execution.

But wait, there's more! OpenCommands doesn't just give you the power to automate your command-line instructions - it also lets you customize when and where those commands are executed.

Want to run a command only when certain file types are opened? OpenCommands has got you covered! Just specify which file type you want to target, and let the plugin handle the rest.

Or maybe you only want your commands to run when the model name matches a specific regular expression? No problem at all! With OpenCommands, you can set up your custom commands to only execute under the exact conditions you specify.

So what are you waiting for? Get OpenCommands today and start automating your command-line tasks like a boss!

### Installation
OpenCommands can be installed from the <a href="https://cxtoolshed.rbvi.ucsf.edu/apps/chimeraxopencommands">toolshed</a> within ChimeraX.


### Instructions
You can set up commands in the "Open Commands" settings (Favorites/Preferences &rarr; Settings... &rarr; Open Commands). Click "add new condition" to define a new set of commands targeting a different file type or name RegEx. If both a RegEx and file type are specified, the model must match both. 

For ChimeraX commands, use `#X` in place of the model ID of whatever structure just opened. For Python code, the `model` and `session` objects are available. Choose between ChimeraX commands and Python with the corresponding icon in the 'type' column in the settings.

Commands and code can be multiple lines long. For commands, each line is executed separately. It will probably be easier to draft long commands/code in a text editor, and then paste that in the Open Commands settings.
