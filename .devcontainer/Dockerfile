FROM nixos/nix:latest

RUN mkdir -p /etc/nix \
    && printf '%s\n' 'experimental-features = nix-command flakes' > /etc/nix/nix.conf

RUN printf '%s\n' \
    'case "$-" in' \
    '  *i*)' \
    '    if [ -z "${IN_NIX_SHELL:-}" ] && [ -f flake.nix ]; then' \
    '      exec nix develop "path:$PWD" --command bash -l' \
    '    fi' \
    '    ;;' \
    'esac' \
    > /root/.bash_profile
