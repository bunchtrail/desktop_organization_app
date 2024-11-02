import sys
import time
import argparse
from config_manager import load_config, save_config
from monitor import start_monitoring
from file_sorter import sort_desktop
from logger import get_logger

logger = get_logger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Desktop Organizer")
    parser.add_argument('--sort', action='store_true', help='Sort desktop immediately')
    parser.add_argument('--monitor', action='store_true', help='Start monitoring desktop and sorting files automatically')
    parser.add_argument('--set-interval', type=int, help='Set the interval (in seconds) for checking the desktop')
    parser.add_argument('--add-rule', metavar=('TYPE', 'EXTENSION', 'FOLDER'), nargs=3, help='Add a new sorting rule (extension or date, extension, folder name)')
    parser.add_argument('--list-rules', action='store_true', help='List current sorting rules')
    parser.add_argument('--remove-rule', type=str, help='Remove a sorting rule by extension')
    parser.add_argument('--log-level', type=str, help='Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')

    args = parser.parse_args()
    config = load_config()

    if args.set_interval is not None:
        config['check_interval'] = args.set_interval
        save_config(config)
        logger.info("Check interval set to %d seconds", args.set_interval)

    if args.add_rule:
        rule_type, extension, folder = args.add_rule
        new_rule = {
            "type": rule_type,
            "extension": extension,
            "folder": folder
        }
        config['sorting_rules'].append(new_rule)
        save_config(config)
        logger.info("Added new rule: %s", new_rule)

    if args.list_rules:
        rules = config.get('sorting_rules', [])
        if rules:
            print("Current sorting rules:")
            for i, r in enumerate(rules, start=1):
                print(f"{i}. Type: {r['type']}, Extension: {r['extension']}, Folder: {r['folder']}")
        else:
            print("No sorting rules found.")

    if args.remove_rule:
        extension_to_remove = args.remove_rule
        rules = config.get('sorting_rules', [])
        new_rules = [r for r in rules if r['extension'].lower() != extension_to_remove.lower()]
        if len(new_rules) < len(rules):
            config['sorting_rules'] = new_rules
            save_config(config)
            logger.info("Removed rule for extension: %s", extension_to_remove)
        else:
            print("No rule found for this extension.")

    if args.log_level:
        config['log_level'] = args.log_level.upper()
        save_config(config)
        logger.info("Log level set to %s", config['log_level'])

    if args.sort:
        sort_desktop()

    if args.monitor:
        start_monitoring()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user.")
            sys.exit(0)

if __name__ == "__main__":
    main()
