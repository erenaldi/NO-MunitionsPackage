"""Test a second longitudinal shelf support outside the lower panel sweep."""
import probe_a_track_support as probe

if __name__ == '__main__':
    probe.WEB = (-300., 250., -44., -42., 88., 93.)
    probe.OUT = probe.ROOT / 'reviews/a_outer_support_probe.json'
    probe.main()
