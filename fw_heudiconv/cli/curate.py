import argparse
import warnings
import flywheel
from collections import defaultdict
from ..convert import apply_heuristic, update_intentions
from ..query import get_sessions, get_seq_info
from heudiconv import utils
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('fwHeuDiConv-curator')

def pretty_string_seqinfo(seqinfo):

    rep = '{protocol_name}: \n\t\t[TR={tr:.2f} TE={te:.4f} ' \
          'shape=({dim1}, {dim2}, {dim3}, {dim4}) ' \
          'image_type={image_type}] ({idnum})\n'
    return rep.format(protocol_name=seqinfo.protocol_name, tr=seqinfo.TR,
                      te=seqinfo.TE, dim1=seqinfo.dim1, dim2=seqinfo.dim2,
                      dim3=seqinfo.dim3, dim4=seqinfo.dim4,
                      image_type=seqinfo.image_type,
                      idnum=seqinfo.series_id)



def convert_to_bids(client, project_label, heuristic_path, subject_labels=None,
                    session_labels=None, dry_run=False):
    """Converts a project to bids by reading the file entries from flywheel
    and using the heuristics to write back to the BIDS namespace of the flywheel
    containers

    Args:
        client (Client): The flywheel sdk client
        project_label (str): The label of the project
        heuristic_path (str): The path to the heuristic file or the name of a
            known heuristic
        subject_code (str): The subject code
        session_label (str): The session label
        dry_run (bool): Print the changes, don't apply them on flywheel
    """

    logger.info("Querying Flywheel server...")
    project_obj = client.projects.find_first('label="{}"'.format(project_label))
    logger.debug('Found project: %s (%s)', project_obj['label'], project_obj.id, )
    sessions = client.get_project_sessions(project_obj.id)
    # filters
    if subject_labels:
        sessions = [s for s in sessions if s.subject['label'] in subject_labels]
    if session_labels:
        sessions = [s for s in sessions if s.label in session_labels]
    logger.debug('Found sessions:\n\t%s',
                 "\n\t".join(['%s (%s)' % (ses['label'], ses.id) for ses in sessions]))

    # Find SeqInfos to apply the heuristic to
    seq_infos = get_seq_info(client, project_label, sessions)
    logger.debug(
        "Found SeqInfos:\n%s",
        "\n\t".join([pretty_string_seqinfo(seq) for seq in seq_infos]))


    logger.info("Loading heuristic file...")
    heuristic = utils.load_heuristic(heuristic_path)

    logger.info("Applying heuristic to query results...")
    to_rename = heuristic.infotodict(seq_infos)

    if not dry_run:
        logger.info("Applying changes to files...")

    intention_map = defaultdict(list)
    if hasattr(heuristic, "IntendedFor"):
        logger.info("Updating IntendedFor fields based on heuristic file")
        intention_map.update(heuristic.IntendedFor)
        logger.debug("Intention map: %s", intention_map)

    for key, val in to_rename.items():
        apply_heuristic(client, key, val, dry_run, intention_map[key])


def get_parser():

    parser = argparse.ArgumentParser(
        description="Use a heudiconv heuristic to curate bids on flywheel")
    parser.add_argument(
        "--project",
        help="The project in flywheel",
        nargs="+",
        required=True
    )
    parser.add_argument(
        "--heuristic",
        help="Path to a heudiconv-style heuristic file",
        required=True
    )
    parser.add_argument(
        "--subject",
        help="The subject label(s)",
        nargs="+",
        default=None
    )
    parser.add_argument(
        "--session",
        help="The session label(s)",
        nargs="+",
        default=None
    )
    parser.add_argument(
        "--verbose",
        help="Print ongoing messages of progress",
        action='store_true',
        default=False
    )
    parser.add_argument(
        "--dry_run",
        help="Don't apply changes",
        action='store_true',
        default=False
    )

    return parser


def main():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fw = flywheel.Client()
    assert fw, "Your Flywheel CLI credentials aren't set!"
    parser = get_parser()
    args = parser.parse_args()

    # Print a lot if requested
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    project_label = ' '.join(args.project)
    convert_to_bids(client=fw,
                    project_label=project_label,
                    heuristic_path=args.heuristic,
                    session_labels=args.session,
                    subject_labels=args.subject,
                    dry_run=args.dry_run)

if __name__ == '__main__':
    main()