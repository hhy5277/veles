/*! @file workflow_loader.h
 *  @brief Header for WorkflowLoader class.
 *  @author Bulychev Egor <e.bulychev@samsung.com>
 *  @version 1.0
 *
 *  @section Notes
 *  This code partially conforms to <a href="http://google-styleguide.googlecode.com/svn/trunk/cppguide.xml">Google C++ Style Guide</a>.
 *
 *  @section Copyright
 *  Copyright 2013 Samsung R&D Institute Russia
 */
#ifndef INC_VELES_WORKFLOW_LOADER_H_
#define INC_VELES_WORKFLOW_LOADER_H_

#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

#include <string>
#include <memory>  // For shared_ptr<>
#include <veles/logger.h>  // NOLINT(*)
#include <veles/workflow.h>  // NOLINT(*)
#include <veles/poison.h>  // NOLINT(*)

#if __GNUC__ >= 4
#pragma GCC visibility push(default)
#endif

struct archive;
namespace YAML {
struct Node;
}  // namespace YAML


namespace YAML {

class Node;

}

namespace Veles {
/// Type that contains Unit properties
typedef std::unordered_map<std::string, std::shared_ptr<void>> PropertiesTable;
/**
 * Structure that contains all required information about unit to construct it
 */
struct UnitDescription {
  /** Unit name*/
  std::string Name;
  /** Unordered map of unit properties*/
  PropertiesTable Properties;
};
/**
 * Structure that contains all required information about workflow to construct it.
 */
struct WorkflowDescription {
  /** Unordered map of workflow properties.
   * Key = std::string, value = std::string*/
  PropertiesTable Properties;
  /** Vector that contain all workflow units.*/
  std::vector<UnitDescription> Units;
};

/**
 * enum with error type or good result
 */
enum WorkflowExtractionError {
  /// Everything is OK.
  kAllGood,
  /// Error occurred when algorithm extracted archive
  kArchiveExtractionError,
  /// Error occurred when algorithm extracted WorkflowDescription from yaml-file
  kWorkflowFromFileExtractionError,
  /// Error occurred when algorithm deleting temporary directory
  kDeletingTempDirectoryError
};

/**
 * Class that contain all functions to extract workflow from archive.
 * */
class WorkflowLoader : protected DefaultLogger<WorkflowLoader,
                                               Logger::COLOR_YELLOW> {
 public:
  friend class WorkflowLoaderTest;

  /// Destructor. Do nothing.
  virtual ~WorkflowLoader() = default;
  /// @brief Main function.
  /**
   * @param[in] archive Name of the archive that contain workflow.
   * @return Return \b false if can't extract workflow from archive.
   *
   *
   * 1) Extract archive (using libarchive) to directory kWorkDirectory.\n   *
   * 2) Read WorkflowDescription from kWorkflowDecompressedFile\n
   * 3) Go through workflow units looking for links to files with weights&\n
   * biases. If find key that content "link_to_" -> extract files (using zlib)\n
   * 4) Read bin-files to arrays of float, add arrays to WorkflowDescription\n
   * 6) Delete kWorkDirectory with all files.\n
   */
  void Load(const std::string& archive);
  /**
   * @brief Print structure of workflow (without float arrays).
   *
   * @param[in] workflow Structure of this workflow will be printed.
   *
   *  1) Go through unordered map of workflow properties.
   *  @code
   *    for (auto& x : workflow.Properties) {
   *      std::cout << x.first << ": " << x.second << std::endl;
     *    }
   *  @endcode
   *  2) Go through vector of unit and print unit name and properties.
   *  @code
   * for (unsigned i = 0; i < workflow.Units.size(); ++i)
   * {
   *   std::cout << "\nUnit name: " << workflow.Units.at(i).Name << std::endl;
   *   for (auto& y : workflow.Units.at(i).Properties)
   *   {
   *    std::cout << y.first << ": " <<
   *    static_cast<std::string*>(y.second.get())->c_str() << std::endl;
   *   }
   * }
   *  @endcode
   * */
  std::string PrintWorkflowStructure();
  Workflow GetWorkflow();
  WorkflowDescription GetWorkflowDescription() const { return workflow_desc_; }

  void InitializeWorkflow();

 protected:
  const WorkflowDescription& workflow_desc() const;

 private:
  /// @brief Extract file archive.
  /**
   * @param[in] filename Name of the archive that should be extracted.
   * @param[in] directory Name of the directory where will be extracted archive.
   *
   * Function that extract file archive (with name = \b filename) to directory with
   * name = \b directory.
   **/
  void ExtractArchive(const std::string& filename,
                      const std::string& directory = kWorkingDirectory);

  /**
   * @brief Extract workflow from yaml file.
   *
   * @param[in] yaml_filename Name of yaml file that contain info about workflow.
   *
   * @return Return \b false if can't extract workflow from yaml file.
   *
   * Open yaml file (or print error if it not possible)
   * */
  void InitWorkflow() {
    auto temp = std::string(kWorkingDirectory) + kWorkflowDecompressedFile;
    GetWorkflow(temp);
  }

  void GetWorkflow(const std::string& yaml_filename);
  /// @brief Extract structure of workflow from YAML::Node
  /**
   * @param[in] workflow In this workflow function will save info from YAML::Node.
   * @param[in] doc From this YAML::Node function will extract workflow.
   * @return Return \b false if can't extract workflow from YAML::Node.
   *
   * Function go through YAML::Node and extract info about workflow.
   */
  void CreateWorkflow(const YAML::Node& doc);
  /// @brief Extract structure of unit from YAML::Node
  /**
   * @param[in] unit Function will save info from YAML::Node to it.
   * @param[in] doc From this YAML::Node function will extract unit.
   * @return Return \b false if can't extract unit from YAML::Node.
   *
   * Function go through YAML::Node and extract info about unit. An if it's
   * needed extract files with float arrays and read them to structure.
   */
  void GetUnit(const YAML::Node& doc, UnitDescription* unit);
  std::shared_ptr<void> GetProperties(const YAML::Node& node);
  std::shared_ptr<float> GetArrayFromFile(const std::string& file,
                                          size_t* arr_size);
  /// @brief Remove directory with all files (not directories) inside.
  /**
   * @param[in] path Path to directory that will be deleted.
   * @return Return \b false if directory can't be deleted because of bad path
   * or permissions or directory inside.
   */
  void RemoveDirectory(const std::string& path);

  /// @brief Some function for ExtractArchive
  int  CopyData(const archive& ar, archive *aw);

  /// Default path to working directory.
  static const char* kWorkingDirectory;
  /// Default name of decompressed yaml file.
  static const char* kWorkflowDecompressedFile;

  WorkflowDescription workflow_desc_;
  Workflow workflow_;
  // Variable to save path + name of archive with info about workflow
  std::string archive_name_;
  std::string file_with_workflow_;
};

}  // namespace Veles

#if __GNUC__ >= 4
#pragma GCC visibility pop
#endif

#endif  // INC_VELES_WORKFLOW_LOADER_H_
