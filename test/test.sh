select option in "Update Openaibot" "Skip Openaibot Update"; do
  case $option in
  "Update Openaibot")
    # Change directory to the project
    cd Openaibot || exit

    # Update the Openaibot project
    git pull

    # Exit the menu
    break
    ;;
  "Skip Openaibot Update")
    # Exit the menu and continue with installation
    break
    ;;
  *)
    echo "Invalid option. Please select a valid option."
    ;;
  esac
done
