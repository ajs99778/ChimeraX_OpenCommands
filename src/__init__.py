import re
from io import StringIO

from chimerax.core.commands import run
from chimerax.core.scripting import open_python_script
from chimerax.core.toolshed import BundleAPI
from chimerax.core.models import ADD_MODELS

class _OpenCommands_API(BundleAPI):

    api_version = 1

    @staticmethod
    def initialize(session, bundle_info):
        """
        custom initialization sets settings, applies AaronTools environment
        variables, registers substituent selectors, menu stuff, 
        mouse modes, and changes the output destination for AaronTools loggers
        """
        from OpenCommands import settings as openCommands_settings
        openCommands_settings.settings = settings._openCommandsSettings(session, "OpenCommands")
        if session.ui.is_gui:
            session.ui.triggers.add_handler(
                'ready',
                lambda *args, ses=session: settings.register_settings_options(ses)
            )

        session.open_command_settings = openCommands_settings
        if openCommands_settings.settings.version == 1:
            new_data = []
            for (format_name, name_regex, cmd_type, format_commands) in openCommands_settings.settings.DATA:
                new_data.append(
                    [format_name, name_regex, cmd_type, format_commands, "parent"]
                )
            openCommands_settings.settings.DATA = new_data
            openCommands_settings.settings.version = 2
            openCommands_settings.settings.save()
        
        session.triggers.add_handler(ADD_MODELS, _OpenCommands_API.run_commands)

    @staticmethod
    def run_commands(trigger_name, models):
        for model in models:
            try:
                if not model.session:
                    continue
                settings = model.session.open_command_settings.settings
                for (format_name, name_regex, cmd_type, format_commands, model_group) in settings.DATA:
                    # go through each set of conditions and run the command/code
                    # if it applies to this model
                    if model_group == "parent" and model.parent is not model.session.models.scene_root_model:
                        continue

                    if name_regex.strip() and not re.search(name_regex.strip(), model.name):
                        continue

                    apply_to_models = [model]
                    if model_group != "parent" and model.child_models():
                        for mdl in model.child_models():
                            if _OpenCommands_API.format_acceptable(mdl, format_name):
                                apply_to_models.append(mdl)
                        
                        if model_group != "any" and not _OpenCommands_API.format_acceptable(model, format_name):
                            apply_to_models.pop(0)

                    elif model_group == "parent" and model.child_models():
                        for mdl in model.child_models():
                            if _OpenCommands_API.format_acceptable(mdl, format_name):
                                break
                        else:
                            continue
                    
                    for mdl in apply_to_models:
                        if cmd_type == "command":
                            for cmd in format_commands.splitlines():
                                run(mdl.session, cmd.replace("#X", mdl.atomspec))
    
                        elif cmd_type == "python":
                            try:
                                exec(format_commands, {"session": mdl.session, "model": mdl})
                            except Exception as e:
                                error_msg = "error while executing python open code for file type %s" % format_name
                                if name_regex.strip():
                                    error_msg += " with name matching %s" % name_regex
                                error_msg += ":\n"
                                error_msg += str(e)
                                mdl.session.logger.error(error_msg)
            
            except AttributeError as e:
                continue

    @staticmethod
    def format_acceptable(mdl, format_name):
        mdl_format = mdl.opened_data_format
        if not mdl_format:
            return False
        if format_name == "Any":
            return True
        if format_name == mdl_format.name:
            return True
        return False


bundle_api = _OpenCommands_API()
