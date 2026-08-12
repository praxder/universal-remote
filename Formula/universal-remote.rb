class UniversalRemote < Formula
  desc "Local, terminal-based universal TV remote"
  homepage "https://github.com/RightNowMinistries/universal-remote"
  # PLACEHOLDER until the first release cut from this repository. The release
  # pipeline's `tap` job (.github/workflows/release.yml, in this repo) rewrites
  # the version in `url`, the `version` line, and the `sha256` line below on
  # every release. The values here still describe the last asset published from
  # praxder/universal-remote, so `brew install` will NOT work from this tap
  # until that first rewrite lands a real asset + checksum.
  url "https://github.com/RightNowMinistries/universal-remote/releases/download/v2.0.0/universal-remote-macos-arm64.tar.gz"
  version "2.0.0"
  sha256 "725eb51aa04a6474560429b3fb79dba6d8bc1584f934651e2b932101799e6ef2"
  license "MIT"

  depends_on arch: :arm64

  def install
    libexec.install Dir["*"]
    bin.install_symlink libexec/"universal-remote"
    # Short alias: `ur` resolves to the same launcher.
    bin.install_symlink libexec/"universal-remote" => "ur"
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/universal-remote --version")
    assert_match version.to_s, shell_output("#{bin}/ur --version")
  end
end
