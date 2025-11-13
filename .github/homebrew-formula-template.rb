# This is a template for the Homebrew formula that gets automatically
# generated and pushed to https://github.com/conallob/homebrew-tap
#
# The release workflow replaces __VERSION__, __TAG__, and __SHA256__ placeholders
# DO NOT manually edit the generated formula in homebrew-tap

class OmnifocusScripts < Formula
  desc "Collection of AppleScript and Python tools to automate OmniFocus workflows and integrate with services like Slack"
  homepage "https://github.com/conallob/omnifocus-scripts"
  url "https://github.com/conallob/omnifocus-scripts/archive/__TAG__.tar.gz"
  sha256 "__SHA256__"
  version "__VERSION__"
  license "BSD-3-Clause"

  depends_on :macos

  def install
    # Install all scripts to share directory
    share.install Dir["*"]

    # Create symlink for easy access
    (prefix/"omnifocus-scripts").install_symlink share
  end

  def caveats
    <<~EOS
      OmniFocus scripts have been installed to:
        #{opt_share}

      Available integrations can be found in subdirectories.
      See #{opt_share}/README.md for complete documentation.

      Quick start:
        cd #{opt_share}
        cat README.md
    EOS
  end

  test do
    assert_predicate share/"README.md", :exist?
    assert_predicate share/"LICENSE", :exist?
    # Verify at least one integration exists
    assert Dir.glob("#{share}/*").any? { |d| File.directory?(d) && !File.basename(d).start_with?(".") }
  end
end
