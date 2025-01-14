import re
from io import StringIO
from time import sleep

from chimerax.core.commands import run
from chimerax.core.scripting import open_python_script
from chimerax.core.toolshed import BundleAPI
from chimerax.core.models import ADD_MODELS

from Qt.QtCore import QThread

class _OpenCommands_API(BundleAPI):

    api_version = 1
    threads = []

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
        
        if openCommands_settings.settings.version == 2:
            new_data = []
            for (format_name, name_regex, cmd_type, format_commands, model_group) in settings.DATA:
                new_data.append(
                    [format_name, name_regex, cmd_type, format_commands, model_group.lower()]
                )
            openCommands_settings.settings.DATA = new_data
            openCommands_settings.settings.version = 3
            openCommands_settings.settings.save()
        
        session.triggers.add_handler(ADD_MODELS, _OpenCommands_API.run_commands)

    @staticmethod
    def run_commands(trigger_name, models):
        for model in models:
            if model.deleted:
                continue
            try:
                if not model.session:
                    continue
                settings = model.session.open_command_settings.settings
                if settings.debug:
                    model.session.logger.info(
                        "debugging is enabled in your OpenCommands settings"
                    )
                    model.session.logger.info(
                        "<pre>checking commands for %s %s</pre>" % (model.name, model.atomspec),
                        is_html=True
                    )
                for (format_name, name_regex, cmd_type, format_commands, model_group) in settings.DATA:
                    if settings.debug:
                        model.session.logger.info(
                            "<pre>checking option with these criteria:\n\tformat_name: %s\n\tRegEx: %s\n\ttype: %s\n\tmodel group: %s\n\tcommands:\n%s</pre>" % (format_name, name_regex, cmd_type, model_group, format_commands),
                            is_html=True
                        )
                    # go through each set of conditions and run the command/code
                    # if it applies to this model
                    if model_group == "top parent" and model.parent is not model.session.models.scene_root_model:
                        if setting.debug:
                            model.session.logger.info(
                                "<pre>\tmodel is not top parent</pre>",
                                is_html=True
                            )
                        continue

                    check_models = []
                    if model_group in {"top parent", "parent", "any"}:
                        if settings.debug:
                            model.session.logger.info(
                                "<pre>\twill check child models (%i children)</pre>" % len(model.child_models()),
                                is_html=True
                            )
                        for m in model.child_models():
                            check_models.append(m)
                    
                    if model_group in {"this", "any", "children"}:
                        check_models.append(model)

                    apply_to_models = set()
                    for m in check_models:
                        if settings.debug:
                            model.session.logger.info(
                                "<pre>checking %s %s</pre>" % (m.name, m.atomspec),
                                is_html=True
                            )
                        
                        if name_regex.strip() and not re.search(name_regex.strip(), m.name):
                            if settings.debug:
                                model.session.logger.info(
                                    "<pre>\tname regex %s doesn't match</pre>" % name_regex,
                                    is_html=True
                                )
                            continue
                        elif settings.debug:
                            model.session.logger.info(
                                "<pre>\tname regex %s matches %s</pre>" % (name_regex, re.search(name_regex.strip(), m.name).group(0)),
                                is_html=True
                            )
    
                        if not _OpenCommands_API.format_acceptable(m, format_name):
                            if settings.debug:
                                model.session.logger.info(
                                    "<pre>\tfile type is wrong or not specified (%s)</pre>" % format_name,
                                    is_html=True
                                )
                            continue
                        elif settings.debug:
                            model.session.logger.info(
                                "<pre>\tfile type %s is acceptable</pre>" % m.opened_data_format,
                                is_html=True
                            )
    
                        if model_group in {"top parent", "parent", "any"}:
                            apply_to_models.add(m.parent)
                        
                        if model_group in {"this", "any"}:
                            apply_to_models.add(m)
                        
                        if model_group in {"any", "children"}:
                            for child in m.child_models():
                                apply_to_models.append(child)

                    for m in apply_to_models:
                        if settings.debug:
                            model.session.logger.info("applying command to %s %s" % (m.name, m.atomspec))
                        if cmd_type == "command":
                            for cmd in format_commands.splitlines():
                                _OpenCommands_API._exec(m.session, cmd.replace("#X", m.atomspec))
                                # thread = DelayOpenCommands()
                                # thread.finished.connect(
                                #     lambda ses=m.session, c=cmd.replace("#X", m.atomspec):
                                #     _OpenCommands_API._exec(ses, c)
                                # )
                                # _OpenCommands_API.threads.append(thread)
                                # thread.start()
        
                        elif cmd_type == "python":
                            try:
                                exec(format_commands, {"session": m.session, "model": m})
                            except Exception as e:
                                error_msg = "error while executing python open code for file type %s" % format_name
                                if name_regex.strip():
                                    error_msg += " with name matching %s" % name_regex
                                error_msg += ":\n"
                                error_msg += str(e)
                                m.session.logger.error(error_msg)
            
            except AttributeError as e:
                continue

    @staticmethod
    def _exec(session, command):
        run(session, command)

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


class DelayOpenCommands(QThread):
    def run(self):
        sleep(1)


bundle_api = _OpenCommands_API()
