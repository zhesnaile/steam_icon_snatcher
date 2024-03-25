{
  description = "snatch game images";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { system = "x86_64-linux"; config.allowUnfree = true; };
        python-packages = p: with p; [
          requests
          vdf
          loguru
        ];
        python-with-packages = pkgs.python311.withPackages(python-packages);
      in
      {
        devShell = pkgs.mkShell {
          buildInputs = with pkgs; [
            python-with-packages
            steamcmd
          ];

          shellHook = ''
            echo "Welcome to the development environment!"
          '';
        };
      });
}
