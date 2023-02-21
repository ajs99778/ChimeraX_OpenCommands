import re

from chimerax.core.commands import run
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
        
        session.triggers.add_handler(ADD_MODELS, _OpenCommands_API.run_commands)

    @staticmethod
    def run_commands(trigger_name, models):
        for model in models:
            settings = model.session.open_command_settings.settings
            if not model.session:
                continue
            try:
                file_format = model.opened_data_format
                if file_format is None:
                    continue
                format_type = file_format.name
                for (format_name, name_regex, format_commands) in settings.DATA:
                    print(format_name, name_regex, format_commands)
                    if model.filename and name_regex.strip() and not (
                        re.search(name_regex.strip(), model.filename)
                    ):
                        continue
                    if format_name != "Any" and format_name != format_type:
                        continue
                    for cmd in format_commands.splitlines():
                        run(model.session, cmd.replace("${i}", model.atomspec))
            
            except AttributeError:
                continue


bundle_api = _OpenCommands_API()
