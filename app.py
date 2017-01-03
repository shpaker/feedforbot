import logging
import pyfeedstg


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        filename="log.txt",
                        format='%(asctime)s [%(levelname)-8s] %(message)s')
    logging.info('\n\n======== RUN SERVER ========\n')
    pyfeedstg.Server().run()
