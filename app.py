import argparse
import logging

from pyfeedstg import Server


if __name__ == '__main__':
    appDescription = 'Forwarding articles from RSS/Atom feeds to Telegram'
 
    parser = argparse.ArgumentParser(description=appDescription)
    parser.add_argument('-c', '--config',
                        default='config.yml',
                        help='Choose file with bot\'s configuration')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Switch logging to DEBUG')
    parser.add_argument('-l', '--last', action='store_true',
                        help='Send last entry in feed')
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s [%(levelname)-8s] %(message)s')
    logger = logging.getLogger()
    if args.debug:
        logger.setLevel(level=logging.DEBUG)
    else:
        logger.setLevel(level=logging.INFO)

    logging.info('Start server with "{}" configuration'.format(args.config))
    try:
        Server(filename=args.config, sendLastEntry=args.last).run()
    except Exception as err:
        logging.error('ERROR: {}'.format(err))
