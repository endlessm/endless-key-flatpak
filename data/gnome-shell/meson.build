gnome_shell_search_providers_dir = join_paths(datadir, 'gnome-shell', 'search-providers')

configure_file(
    input: 'org.learningequality.Kolibri.ini.in',
    output: base_application_id + '.ini',
    configuration: kolibri_app_config,
    install_dir: gnome_shell_search_providers_dir
)
